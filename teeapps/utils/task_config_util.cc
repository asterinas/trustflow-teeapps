// Copyright 2023 Ant Group Co., Ltd.
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//   http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

#include "teeapps/utils/task_config_util.h"

#include "yacl/base/exception.h"

#include "teeapps/utils/data_uri_util.h"
#include "teeapps/utils/io_util.h"
#include "teeapps/utils/json2pb.h"

#include "secretflow/spec/v1/data.pb.h"
#include "teeapps/proto/params/biclassifier_evaluation.pb.h"
#include "teeapps/proto/params/dataset_filter.pb.h"
#include "teeapps/proto/params/dataset_split.pb.h"
#include "teeapps/proto/params/lr_hyper_params.pb.h"
#include "teeapps/proto/params/predict.pb.h"
#include "teeapps/proto/params/prediction_bias_eval.pb.h"
#include "teeapps/proto/params/psi.pb.h"
#include "teeapps/proto/params/stats_corr_params.pb.h"
#include "teeapps/proto/params/vif_params.pb.h"
#include "teeapps/proto/params/woe_binning.pb.h"
#include "teeapps/proto/params/xgb_hyper_params.pb.h"

namespace teeapps {
namespace utils {

namespace {
void AdjustTableSchema(
    secretflow::spec::v1::TableSchema* table_schema,
    const google::protobuf::RepeatedPtrField<std::string> labels,
    const google::protobuf::RepeatedPtrField<std::string> ids) {
  int index;
  for (const std::string& id : ids) {
    index = -1;
    for (int i = 0; i < table_schema->features_size(); i++) {
      if (id == table_schema->features(i)) {
        index = i;
        break;
      }
    }
    if (index != -1) {
      table_schema->add_ids(id);
      table_schema->add_id_types(table_schema->feature_types(index));

      table_schema->mutable_features()->erase(
          table_schema->mutable_features()->begin() + index);
      table_schema->mutable_feature_types()->erase(
          table_schema->mutable_feature_types()->begin() + index);
    }
  }

  for (const std::string& label : labels) {
    index = -1;
    for (int i = 0; i < table_schema->features_size(); i++) {
      if (label == table_schema->features(i)) {
        index = i;
        break;
      }
    }
    if (index != -1) {
      table_schema->add_labels(label);
      table_schema->add_label_types(table_schema->feature_types(index));

      table_schema->mutable_features()->erase(
          table_schema->mutable_features()->begin() + index);
      table_schema->mutable_feature_types()->erase(
          table_schema->mutable_feature_types()->begin() + index);
    }
  }
}
}  // namespace

class TaskConfigFiller {
 public:
  virtual ~TaskConfigFiller(){};
  virtual void Fill(
      teeapps::TaskConfig& task_config,
      const secretflow::spec::v1::ComponentDef& component_def,
      const teeapps::component::EvalParamReader& eval_param_reader) = 0;
};

class PsiConfigFiller : public TaskConfigFiller {
 public:
  void Fill(
      teeapps::TaskConfig& task_config,
      const secretflow::spec::v1::ComponentDef& component_def,
      const teeapps::component::EvalParamReader& eval_param_reader) override {
    teeapps::params::PsiParams params;
    for (int i = 0; i < component_def.inputs_size(); i++) {
      const auto& input_keys =
          eval_param_reader
              .GetInputAttrs(component_def.inputs(i).name(),
                             component_def.inputs(i).attrs(0).name())
              .ss();
      teeapps::params::PsiParams::PsiKey psi_key;
      psi_key.set_table_name(
          eval_param_reader.GetInput(component_def.inputs(i).name()).name());
      for (const auto& input_key : input_keys) {
        psi_key.add_keys(input_key);
      }
      // If keys not provided, ids of the dataset will be used.
      if (psi_key.keys_size() == 0) {
        psi_key.mutable_keys()->Add(
            task_config.inputs(i).schema().ids().begin(),
            task_config.inputs(i).schema().ids().end());
      }
      *(params.add_psi_keys()) = std::move(psi_key);
    }
    task_config.mutable_params()->PackFrom(std::move(params));
    task_config.mutable_params()->set_type_url(
        "type.googleapis.com/teeapps.params.PsiParams");
  }
};

class FeatureFilterFiller : public TaskConfigFiller {
 public:
  void Fill(
      teeapps::TaskConfig& task_config,
      const secretflow::spec::v1::ComponentDef& component_def,
      const teeapps::component::EvalParamReader& eval_param_reader) override {
    teeapps::params::DatasetFilterParams params;
    const auto drop_features_iter =
        eval_param_reader
            .GetInputAttrs(component_def.inputs(0).name(),
                           component_def.inputs(0).attrs(0).name())
            .ss();
    params.mutable_drop_features()->Add(drop_features_iter.begin(),
                                        drop_features_iter.end());
    task_config.mutable_params()->PackFrom(std::move(params));
    task_config.mutable_params()->set_type_url(
        "type.googleapis.com/teeapps.params.DatasetFilterParams");
  }
};

class DatasetSplitFiller : public TaskConfigFiller {
 public:
  void Fill(
      teeapps::TaskConfig& task_config,
      const secretflow::spec::v1::ComponentDef& component_def,
      const teeapps::component::EvalParamReader& eval_param_reader) override {
    teeapps::params::DatasetSplitParams params;
    YACL_ENFORCE(component_def.attrs_size() == 4,
                 "train_test_split attrs size should be 4, got {}",
                 component_def.attrs_size());
    // train_size
    const float train_size =
        eval_param_reader.GetAttr(component_def.attrs(0).name()).f();
    params.set_training_data_ratio(train_size);
    // should fix random
    const bool should_fix_random =
        eval_param_reader.GetAttr(component_def.attrs(1).name()).b();
    params.set_should_fix_random(should_fix_random);
    // random_state
    const int64_t random_state =
        eval_param_reader.GetAttr(component_def.attrs(2).name()).i64();
    params.set_random_state(random_state);
    // shuffle
    const bool shuffle =
        eval_param_reader.GetAttr(component_def.attrs(3).name()).b();
    params.set_shuffle(shuffle);
    task_config.mutable_params()->PackFrom(std::move(params));
    task_config.mutable_params()->set_type_url(
        "type.googleapis.com/teeapps.params.DatasetSplitParams");
  }
};

class PearsonrFiller : public TaskConfigFiller {
 public:
  void Fill(
      teeapps::TaskConfig& task_config,
      const secretflow::spec::v1::ComponentDef& component_def,
      const teeapps::component::EvalParamReader& eval_param_reader) override {
    teeapps::params::StatsCorrParams params;
    const auto& feature_selects_iter =
        eval_param_reader
            .GetInputAttrs(component_def.inputs(0).name(),
                           component_def.inputs(0).attrs(0).name())
            .ss();
    params.mutable_feature_selects()->Add(feature_selects_iter.begin(),
                                          feature_selects_iter.end());
    task_config.mutable_params()->PackFrom(std::move(params));
    task_config.mutable_params()->set_type_url(
        "type.googleapis.com/teeapps.params.StatsCorrParams");
  }
};

class VifFiller : public TaskConfigFiller {
 public:
  void Fill(
      teeapps::TaskConfig& task_config,
      const secretflow::spec::v1::ComponentDef& component_def,
      const teeapps::component::EvalParamReader& eval_param_reader) override {
    teeapps::params::VifParams params;
    const auto& feature_selects_iter =
        eval_param_reader
            .GetInputAttrs(component_def.inputs(0).name(),
                           component_def.inputs(0).attrs(0).name())
            .ss();
    params.mutable_feature_selects()->Add(feature_selects_iter.begin(),
                                          feature_selects_iter.end());
    task_config.mutable_params()->PackFrom(std::move(params));
    task_config.mutable_params()->set_type_url(
        "type.googleapis.com/teeapps.params.VifParams");
  }
};

class TableStatisticsFiller : public TaskConfigFiller {
 public:
  void Fill(
      teeapps::TaskConfig& task_config,
      const secretflow::spec::v1::ComponentDef& component_def,
      const teeapps::component::EvalParamReader& eval_param_reader) override {}
};

class WoeBinningFiller : public TaskConfigFiller {
 public:
  void Fill(
      teeapps::TaskConfig& task_config,
      const secretflow::spec::v1::ComponentDef& component_def,
      const teeapps::component::EvalParamReader& eval_param_reader) override {
    teeapps::params::WoeBinningParams params;
    YACL_ENFORCE(component_def.attrs_size() == 3,
                 "vert_woe_binning attrs size should be 3, got {}",
                 component_def.attrs_size());

    teeapps::params::WoeBinningParams::FeatureBinningConf binning_config;

    // binning_method
    const std::string binning_method =
        eval_param_reader.GetAttr(component_def.attrs(0).name()).s();
    binning_config.set_binning_method(binning_method);
    // positive_label
    const std::string positive_label =
        eval_param_reader.GetAttr(component_def.attrs(1).name()).s();
    params.set_positive_label(positive_label);
    // bin_num
    const int64_t bin_num =
        eval_param_reader.GetAttr(component_def.attrs(2).name()).i64();
    binning_config.set_n_divide(bin_num);
    // feature selects
    const auto feature_selects =
        eval_param_reader
            .GetInputAttrs(component_def.inputs(0).name(),
                           component_def.inputs(0).attrs(0).name())
            .ss();
    for (const auto& feature_select : feature_selects) {
      binning_config.set_feature(feature_select);
      *(params.add_feature_binning_confs()) = binning_config;
      params.add_feature_selects(feature_select);
    }

    const auto labels =
        eval_param_reader
            .GetInputAttrs(component_def.inputs(0).name(),
                           component_def.inputs(0).attrs(1).name())
            .ss();
    AdjustTableSchema(task_config.mutable_inputs(0)->mutable_schema(), labels,
                      google::protobuf::RepeatedPtrField<std::string>());

    task_config.mutable_params()->PackFrom(std::move(params));
    task_config.mutable_params()->set_type_url(
        "type.googleapis.com/teeapps.params.WoeBinningParams");
  }
};

class WoeSubstitutionFiller : public TaskConfigFiller {
 public:
  void Fill(
      teeapps::TaskConfig& task_config,
      const secretflow::spec::v1::ComponentDef& component_def,
      const teeapps::component::EvalParamReader& eval_param_reader) override {}
};

class XgbTrainFiller : public TaskConfigFiller {
 public:
  void Fill(
      teeapps::TaskConfig& task_config,
      const secretflow::spec::v1::ComponentDef& component_def,
      const teeapps::component::EvalParamReader& eval_param_reader) override {
    teeapps::params::XgbHyperParams params;
    YACL_ENFORCE(component_def.attrs_size() == 16,
                 "xgb_train attrs size should be 16, got {}",
                 component_def.attrs_size());
    // num_boost_round
    const int64_t num_boost_round =
        eval_param_reader.GetAttr(component_def.attrs(0).name()).i64();
    params.set_num_boost_round(num_boost_round);
    // max_depth
    const int64_t max_depth =
        eval_param_reader.GetAttr(component_def.attrs(1).name()).i64();
    params.set_max_depth(max_depth);
    // max_leaves
    const int64_t max_leaves =
        eval_param_reader.GetAttr(component_def.attrs(2).name()).i64();
    params.set_max_leaves(max_leaves);
    // seed
    const int64_t seed =
        eval_param_reader.GetAttr(component_def.attrs(3).name()).i64();
    params.set_seed(seed);
    // learning_rate
    const float learning_rate =
        eval_param_reader.GetAttr(component_def.attrs(4).name()).f();
    params.set_learning_rate(learning_rate);
    // lambda
    const float lambda =
        eval_param_reader.GetAttr(component_def.attrs(5).name()).f();
    params.set_lambda(lambda);
    // gamma
    const float gamma =
        eval_param_reader.GetAttr(component_def.attrs(6).name()).f();
    params.set_gamma(gamma);
    // colsample_bytree
    const float colsample_bytree =
        eval_param_reader.GetAttr(component_def.attrs(7).name()).f();
    params.set_colsample_bytree(colsample_bytree);
    // base_score
    const float base_score =
        eval_param_reader.GetAttr(component_def.attrs(8).name()).f();
    params.set_base_score(base_score);
    // min_child_weight
    const float min_child_weight =
        eval_param_reader.GetAttr(component_def.attrs(9).name()).f();
    params.set_min_child_weight(min_child_weight);
    // objective
    const std::string objective =
        eval_param_reader.GetAttr(component_def.attrs(10).name()).s();
    params.set_objective(objective);
    // alpha
    const float alpha =
        eval_param_reader.GetAttr(component_def.attrs(11).name()).f();
    params.set_alpha(alpha);
    // subsample
    const float subsample =
        eval_param_reader.GetAttr(component_def.attrs(12).name()).f();
    params.set_subsample(subsample);
    // max_bin
    const int64_t max_bin =
        eval_param_reader.GetAttr(component_def.attrs(13).name()).i64();
    params.set_max_bin(max_bin);
    // tree_method
    const std::string tree_method =
        eval_param_reader.GetAttr(component_def.attrs(14).name()).s();
    params.set_tree_method(tree_method);
    // booster
    const std::string booster =
        eval_param_reader.GetAttr(component_def.attrs(15).name()).s();
    params.set_booster(booster);

    const auto ids = eval_param_reader
                         .GetInputAttrs(component_def.inputs(0).name(),
                                        component_def.inputs(0).attrs(0).name())
                         .ss();

    const auto labels =
        eval_param_reader
            .GetInputAttrs(component_def.inputs(0).name(),
                           component_def.inputs(0).attrs(1).name())
            .ss();
    AdjustTableSchema(task_config.mutable_inputs(0)->mutable_schema(), labels,
                      ids);

    task_config.mutable_params()->PackFrom(std::move(params));
    task_config.mutable_params()->set_type_url(
        "type.googleapis.com/teeapps.params.XgbHyperParams");
  }
};

class LrTrainFiller : public TaskConfigFiller {
 public:
  void Fill(
      teeapps::TaskConfig& task_config,
      const secretflow::spec::v1::ComponentDef& component_def,
      const teeapps::component::EvalParamReader& eval_param_reader) override {
    teeapps::params::LrHyperParams params;
    YACL_ENFORCE(component_def.attrs_size() == 5,
                 "lr_train attrs size should be 5, got {}",
                 component_def.attrs_size());
    // max_iter
    const int64_t max_iter =
        eval_param_reader.GetAttr(component_def.attrs(0).name()).i64();
    params.set_max_iter(max_iter);
    // reg_type
    const std::string reg_type =
        eval_param_reader.GetAttr(component_def.attrs(1).name()).s();
    params.set_regression_type(reg_type);
    // l2_norm
    const float l2_norm =
        eval_param_reader.GetAttr(component_def.attrs(2).name()).f();
    params.set_l2_norm(l2_norm);
    // tol
    const float tol =
        eval_param_reader.GetAttr(component_def.attrs(3).name()).f();
    params.set_tol(tol);
    const std::string penalty =
        eval_param_reader.GetAttr(component_def.attrs(4).name()).s();
    params.set_penalty(penalty);

    const auto ids = eval_param_reader
                         .GetInputAttrs(component_def.inputs(0).name(),
                                        component_def.inputs(0).attrs(0).name())
                         .ss();

    const auto labels =
        eval_param_reader
            .GetInputAttrs(component_def.inputs(0).name(),
                           component_def.inputs(0).attrs(1).name())
            .ss();
    AdjustTableSchema(task_config.mutable_inputs(0)->mutable_schema(), labels,
                      ids);

    task_config.mutable_params()->PackFrom(std::move(params));
    task_config.mutable_params()->set_type_url(
        "type.googleapis.com/teeapps.params.LrHyperParams");
  }
};

class PredictFiller : public TaskConfigFiller {
 public:
  void Fill(
      teeapps::TaskConfig& task_config,
      const secretflow::spec::v1::ComponentDef& component_def,
      const teeapps::component::EvalParamReader& eval_param_reader) override {
    teeapps::params::PredictionParams params;
    YACL_ENFORCE(component_def.attrs_size() == 6,
                 "Prediction attrs size should be 6, got {}",
                 component_def.attrs_size());
    auto output_control = params.mutable_output_control();
    // pred_name
    const std::string pred_name =
        eval_param_reader.GetAttr(component_def.attrs(0).name()).s();
    output_control->set_score_field_name(pred_name);
    // save_label
    const bool save_label =
        eval_param_reader.GetAttr(component_def.attrs(1).name()).b();
    output_control->set_output_label(save_label);
    // label_name
    const std::string label_name =
        eval_param_reader.GetAttr(component_def.attrs(2).name()).s();
    output_control->set_label_field_name(label_name);
    // save id
    const bool save_id =
        eval_param_reader.GetAttr(component_def.attrs(3).name()).b();
    output_control->set_output_id(save_id);
    // id
    const std::string id_name =
        eval_param_reader.GetAttr(component_def.attrs(4).name()).s();
    output_control->set_id_field_name(id_name);
    const auto col_names =
        eval_param_reader.GetAttr(component_def.attrs(5).name()).ss();
    output_control->mutable_col_names()->Add(col_names.begin(),
                                             col_names.end());

    const auto ids = eval_param_reader
                         .GetInputAttrs(component_def.inputs(0).name(),
                                        component_def.inputs(0).attrs(0).name())
                         .ss();

    const auto labels =
        eval_param_reader
            .GetInputAttrs(component_def.inputs(0).name(),
                           component_def.inputs(0).attrs(1).name())
            .ss();
    AdjustTableSchema(task_config.mutable_inputs(0)->mutable_schema(), labels,
                      ids);

    task_config.mutable_params()->PackFrom(std::move(params));
    task_config.mutable_params()->set_type_url(
        "type.googleapis.com/teeapps.params.PredictionParams");
  }
};

class BiclassificationEvalFiller : public TaskConfigFiller {
 public:
  void Fill(
      teeapps::TaskConfig& task_config,
      const secretflow::spec::v1::ComponentDef& component_def,
      const teeapps::component::EvalParamReader& eval_param_reader) override {
    teeapps::params::BiClassifierEvalParams params;
    // label field
    const std::string label_field_name =
        eval_param_reader
            .GetInputAttrs(component_def.inputs(0).name(),
                           component_def.inputs(0).attrs(0).name())
            .ss(0);
    params.set_label_field_name(label_field_name);
    // score field
    const std::string score_field_name =
        eval_param_reader
            .GetInputAttrs(component_def.inputs(0).name(),
                           component_def.inputs(0).attrs(1).name())
            .ss(0);
    params.set_score_field_name(score_field_name);
    // bucket size
    const int64_t bucket_num =
        eval_param_reader.GetAttr(component_def.attrs(0).name()).i64();
    params.set_bucket_num(bucket_num);
    // min item count per bucket
    const int64_t min_item_cnt_per_bucket =
        eval_param_reader.GetAttr(component_def.attrs(1).name()).i64();
    params.set_min_item_cnt_per_bucket(min_item_cnt_per_bucket);

    task_config.mutable_params()->PackFrom(std::move(params));
    task_config.mutable_params()->set_type_url(
        "type.googleapis.com/teeapps.params.BiClassifierEvalParams");
  }
};

class PredictionBiasFiller : public TaskConfigFiller {
 public:
  void Fill(
      teeapps::TaskConfig& task_config,
      const secretflow::spec::v1::ComponentDef& component_def,
      const teeapps::component::EvalParamReader& eval_param_reader) override {
    teeapps::params::PredictionBiasEvalParams params;
    // label field
    const std::string label_field_name =
        eval_param_reader
            .GetInputAttrs(component_def.inputs(0).name(),
                           component_def.inputs(0).attrs(0).name())
            .ss(0);
    params.set_label_field_name(label_field_name);
    // score field
    const std::string score_field_name =
        eval_param_reader
            .GetInputAttrs(component_def.inputs(0).name(),
                           component_def.inputs(0).attrs(1).name())
            .ss(0);
    params.set_score_field_name(score_field_name);
    // bucket size
    const int64_t bucket_num =
        eval_param_reader.GetAttr(component_def.attrs(0).name()).i64();
    params.set_bucket_num(bucket_num);
    // min item count per bucket
    const int64_t min_item_cnt_per_bucket =
        eval_param_reader.GetAttr(component_def.attrs(1).name()).i64();
    params.set_min_item_cnt_per_bucket(min_item_cnt_per_bucket);
    // bucket method
    const std::string bucket_method =
        eval_param_reader.GetAttr(component_def.attrs(2).name()).s();
    params.set_bucket_method(bucket_method);
    task_config.mutable_params()->PackFrom(std::move(params));
    task_config.mutable_params()->set_type_url(
        "type.googleapis.com/teeapps.params.PredictionBiasEvalParams");
  }
};

class TaskConfigFillerFactory {
 public:
  TaskConfigFillerFactory() {
    fillers.emplace(teeapps::framework::kPsiComp,
                    std::make_unique<PsiConfigFiller>());
    fillers.emplace(teeapps::framework::kFeatureFilterComp,
                    std::make_unique<FeatureFilterFiller>());
    fillers.emplace(teeapps::framework::kTrainTestSplitComp,
                    std::make_unique<DatasetSplitFiller>());
    fillers.emplace(teeapps::framework::kPearsonrComp,
                    std::make_unique<PearsonrFiller>());
    fillers.emplace(teeapps::framework::kVifComp,
                    std::make_unique<VifFiller>());
    fillers.emplace(teeapps::framework::kTableStatisticsComp,
                    std::make_unique<TableStatisticsFiller>());
    fillers.emplace(teeapps::framework::kVertWoeBinningComp,
                    std::make_unique<WoeBinningFiller>());
    fillers.emplace(teeapps::framework::kVertWoeSubstitutionComp,
                    std::make_unique<WoeSubstitutionFiller>());
    fillers.emplace(teeapps::framework::kXgbTrainComp,
                    std::make_unique<XgbTrainFiller>());
    fillers.emplace(teeapps::framework::kLrTrainComp,
                    std::make_unique<LrTrainFiller>());
    fillers.emplace(teeapps::framework::kXgbPredictComp,
                    std::make_unique<PredictFiller>());
    fillers.emplace(teeapps::framework::kLrPredictComp,
                    std::make_unique<PredictFiller>());
    fillers.emplace(teeapps::framework::kBiclassificationEvalComp,
                    std::make_unique<BiclassificationEvalFiller>());
    fillers.emplace(teeapps::framework::kPredictionBiasComp,
                    std::make_unique<PredictionBiasFiller>());
  }

  const std::unique_ptr<TaskConfigFiller>& GetFiller(
      const std::string& comp_name) {
    const auto& filler = fillers.find(comp_name);
    YACL_ENFORCE(filler != fillers.end(),
                 "Can not find TaskConfig filler for {}", comp_name);
    return filler->second;
  }

 private:
  std::unordered_map<std::string, std::unique_ptr<TaskConfigFiller>> fillers;
};

void FillTaskConfigParams(
    teeapps::TaskConfig& task_config,
    const secretflow::spec::v1::ComponentDef& component_def,
    const teeapps::component::EvalParamReader& eval_param_reader) {
  const std::string comp_name = component_def.name();
  TaskConfigFillerFactory fillers_factory;
  SPDLOG_INFO("Try to fill {} config params", comp_name);
  fillers_factory.GetFiller(comp_name)->Fill(task_config, component_def,
                                             eval_param_reader);
  SPDLOG_INFO("Fill {} config params success", comp_name);
}

void AppendTableSchema(secretflow::spec::v1::TableSchema& dest,
                       const secretflow::spec::v1::TableSchema& source) {
  dest.mutable_ids()->Add(source.ids().begin(), source.ids().end());
  dest.mutable_id_types()->Add(source.id_types().begin(),
                               source.id_types().end());
  dest.mutable_features()->Add(source.features().begin(),
                               source.features().end());
  dest.mutable_feature_types()->Add(source.feature_types().begin(),
                                    source.feature_types().end());
  dest.mutable_labels()->Add(source.labels().begin(), source.labels().end());
  dest.mutable_label_types()->Add(source.label_types().begin(),
                                  source.label_types().end());
}

void GenAndDumpTaskConfig(
    const std::string& app_mode,
    const secretflow::spec::v1::ComponentDef& component_def,
    const teeapps::component::EvalParamReader& eval_param_reader) {
  teeapps::TaskConfig task_config;
  const auto op_name =
      teeapps::framework::comp_op_map.find(component_def.name());
  YACL_ENFORCE(op_name != teeapps::framework::comp_op_map.end(),
               "op_name corresponding {} not found", component_def.name());
  task_config.set_app_type(op_name->second);
  // set inputs
  for (const auto& input_def : component_def.inputs()) {
    const auto& input = eval_param_reader.GetInput(input_def.name());
    auto config_input = task_config.add_inputs();
    config_input->set_data_path(GenDataPath(input.name()));
    // init empty schema
    *(config_input->mutable_schema()) =
        std::move(secretflow::spec::v1::TableSchema());
    if (input.type() == teeapps::component::DistDataType::VERTICAL_TABLE) {
      SPDLOG_INFO("Generate Vertical table's schema");
      secretflow::spec::v1::VerticalTable vertical_table;
      input.meta().UnpackTo(&vertical_table);
      for (const auto& schema : vertical_table.schemas()) {
        AppendTableSchema(*(config_input->mutable_schema()), schema);
      }
    } else if (input.type() ==
               teeapps::component::DistDataType::INDIVIDUAL_TABLE) {
      SPDLOG_INFO("Generate Individual table's schema");
      secretflow::spec::v1::IndividualTable individual_table;
      input.meta().UnpackTo(&individual_table);
      AppendTableSchema(*(config_input->mutable_schema()),
                        individual_table.schema());
    } else {
      // sf.model.* sf.rule.* sf.report ...
      SPDLOG_INFO("sf.model.* sf.rule.* sf.report do nothing about schema");
    }

    config_input->set_table_name(input.name());
  }
  // set outputs
  for (const auto& output_def : component_def.outputs()) {
    // uri may contains schema like
    // "dm://output/datasource_id=(\\w+)&&id=(\\w+)&&uri=(\\w+)"
    const auto& uri = eval_param_reader.GetOutputUri(output_def.name());
    auto config_output = task_config.add_outputs();
    std::string _, output_id;
    if (app_mode == teeapps::framework::kAppModeKuscia) {
      teeapps::utils::ParseDmOutputUri(uri, _, output_id, _);
    } else if (app_mode == teeapps::framework::kAppModeLocal) {
      teeapps::utils::ParseLocalOutputUri(uri, output_id, _);
    } else {
      YACL_THROW("app mode {} not support", app_mode);
    }
    config_output->set_data_path(GenDataPath(output_id));
    config_output->set_data_schema_path(GenSchemaPath(output_id));
  }
  FillTaskConfigParams(task_config, component_def, eval_param_reader);
  // save json file
  std::string task_config_json;
  PB2JSON(task_config, &task_config_json);
  teeapps::utils::WriteFile(teeapps::framework::kTaskConfigPath,
                            task_config_json);
  SPDLOG_INFO("Dumping task config json succeed...");
  SPDLOG_DEBUG("Task config json: {}", task_config_json);
}

}  // namespace utils
}  // namespace teeapps
