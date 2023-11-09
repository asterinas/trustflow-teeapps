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

#pragma once
#include <string>
#include <unordered_map>

#include "spdlog/spdlog.h"

#include "teeapps/component/feature/woe_binning_component.h"
#include "teeapps/component/feature/woe_substitution_component.h"
#include "teeapps/component/ml/eval/biclassification_component.h"
#include "teeapps/component/ml/eval/prediction_bias_component.h"
#include "teeapps/component/ml/predict/lr_component.h"
#include "teeapps/component/ml/predict/xgb_component.h"
#include "teeapps/component/ml/train/lr_component.h"
#include "teeapps/component/ml/train/xgb_component.h"
#include "teeapps/component/preprocessing/feature_filter_component.h"
#include "teeapps/component/preprocessing/psi_component.h"
#include "teeapps/component/preprocessing/train_test_split_component.h"
#include "teeapps/component/stats/pearsonr_component.h"
#include "teeapps/component/stats/table_statistics_component.h"
#include "teeapps/component/stats/vif_component.h"

#include "secretflow/spec/v1/component.pb.h"

namespace teeapps {
namespace framework {
// plat
constexpr char kPlatSim[] = "sim";
constexpr char kPlatSgx[] = "sgx";

// app mode
constexpr char kAppModeLocal[] = "local";
constexpr char kAppModeKuscia[] = "kuscia";

// task files path
constexpr char kDirBase[] = "/home/teeapp/task";
constexpr char kTaskConfigPath[] = "/home/teeapp/task/task_config.json";

// sim cmd
constexpr char kSimPyPath[] = "/home/teeapp/python/bin/python3";
constexpr char kSimPyBizPath[] = "/home/teeapp/sim/teeapps/biz";

// component domain
constexpr char kPreProcessingDomain[] = "preprocessing";
constexpr char kStatsDomain[] = "stats";
constexpr char kMlEvalDomain[] = "ml.eval";
constexpr char kMlPredictDomain[] = "ml.predict";
constexpr char kMlTrainDomain[] = "ml.train";
constexpr char kFeatureDomain[] = "feature";

// component name
constexpr char kPsiComp[] = "psi";
constexpr char kFeatureFilterComp[] = "feature_filter";
constexpr char kTrainTestSplitComp[] = "train_test_split";
constexpr char kPearsonrComp[] = "pearsonr";
constexpr char kVifComp[] = "vif";
constexpr char kTableStatisticsComp[] = "table_statistics";
constexpr char kVertWoeBinningComp[] = "vert_woe_binning";
constexpr char kVertWoeSubstitutionComp[] = "vert_woe_substitution";
constexpr char kXgbTrainComp[] = "xgb_train";
constexpr char kLrTrainComp[] = "lr_train";
constexpr char kXgbPredictComp[] = "xgb_predict";
constexpr char kLrPredictComp[] = "lr_predict";
constexpr char kBiclassificationEvalComp[] = "biclassification_eval";
constexpr char kPredictionBiasComp[] = "prediction_bias_eval";

// component version
constexpr char kCompVersion[] = "0.0.1";

// teeapps op_name or app_type
constexpr char kPsiOp[] = "OP_PSI";
constexpr char kDataSetFilterOp[] = "OP_DATASET_FILTER";
constexpr char kDataSetSplitOp[] = "OP_DATASET_SPLIT";
constexpr char kStatsCorrOp[] = "OP_STATS_CORR";
constexpr char kStatsVifOp[] = "OP_STATS_VIF";
constexpr char kTableStatisticsOp[] = "OP_TABLE_STATISTICS";
constexpr char kWoeBinningOp[] = "OP_WOE_BINNING";
constexpr char kWoeSubstitutionOp[] = "OP_WOE_SUBSTITUTION";
constexpr char kXgbOp[] = "OP_XGB";
constexpr char kLrOp[] = "OP_LR";
constexpr char kPredictOp[] = "OP_PREDICT";
constexpr char kBiclassEvalOp[] = "OP_BICLASSIFIER_EVALUATION";
constexpr char kPredBiasOp[] = "OP_PREDICTION_BIAS_EVALUATION";

// py file name
constexpr char kPsiPy[] = "psi.py";
constexpr char kDataSetFilterPy[] = "dataset_filter.py";
constexpr char kDataSetSplitPy[] = "dataset_split.py";
constexpr char kStatsCorrPy[] = "stats_corr.py";
constexpr char kStatsVifPy[] = "stats_vif.py";
constexpr char kTableStatisticsPy[] = "table_statistics.py";
constexpr char kWoeBinningPy[] = "woe_binning.py";
constexpr char kWoeSubstitutionPy[] = "woe_substitution.py";
constexpr char kXgbPy[] = "xgb.py";
constexpr char kLrPy[] = "lr.py";
constexpr char kPredictPy[] = "predict.py";
constexpr char kBiclassEvalPy[] = "biclassifier_evaluation.py";
constexpr char kPredBiasPy[] = "prediction_bias_eval.py";

const std::unordered_map<std::string, std::string> comp_op_map = {
    {kPsiComp, kPsiOp},
    {kFeatureFilterComp, kDataSetFilterOp},
    {kTrainTestSplitComp, kDataSetSplitOp},
    {kPearsonrComp, kStatsCorrOp},
    {kVifComp, kStatsVifOp},
    {kTableStatisticsComp, kTableStatisticsOp},
    {kVertWoeBinningComp, kWoeBinningOp},
    {kVertWoeSubstitutionComp, kWoeSubstitutionOp},
    {kXgbTrainComp, kXgbOp},
    {kLrTrainComp, kLrOp},
    {kXgbPredictComp, kPredictOp},
    {kLrPredictComp, kPredictOp},
    {kBiclassificationEvalComp, kBiclassEvalOp},
    {kPredictionBiasComp, kPredBiasOp}};

const std::unordered_map<std::string, std::string> comp_py_map = {
    {kPsiComp, kPsiPy},
    {kFeatureFilterComp, kDataSetFilterPy},
    {kTrainTestSplitComp, kDataSetSplitPy},
    {kPearsonrComp, kStatsCorrPy},
    {kVifComp, kStatsVifPy},
    {kTableStatisticsComp, kTableStatisticsPy},
    {kVertWoeBinningComp, kWoeBinningPy},
    {kVertWoeSubstitutionComp, kWoeSubstitutionPy},
    {kXgbTrainComp, kXgbPy},
    {kLrTrainComp, kLrPy},
    {kXgbPredictComp, kPredictPy},
    {kLrPredictComp, kPredictPy},
    {kBiclassificationEvalComp, kBiclassEvalPy},
    {kPredictionBiasComp, kPredBiasPy}};

inline std::string GenCompFullName(const std::string& domain,
                                   const std::string& name,
                                   const std::string& version) {
  return fmt::format("{}.{}:{}", domain, name, version);
}

const std::unordered_map<std::string, secretflow::spec::v1::ComponentDef>
    COMP_DEF_LIST = {
        // PreProcessing
        {GenCompFullName(kPreProcessingDomain, kPsiComp, kCompVersion),
         secretflow::spec::v1::ComponentDef(
             *teeapps::component::PsiComponent::GetInstance().Definition())},
        {GenCompFullName(kPreProcessingDomain, kFeatureFilterComp,
                         kCompVersion),
         secretflow::spec::v1::ComponentDef(
             *teeapps::component::FeatureFilterComponent::GetInstance()
                  .Definition())},
        {GenCompFullName(kPreProcessingDomain, kTrainTestSplitComp,
                         kCompVersion),
         secretflow::spec::v1::ComponentDef(
             *teeapps::component::TrainTestSplitComponent::GetInstance()
                  .Definition())},
        // Stats
        {GenCompFullName(kStatsDomain, kPearsonrComp, kCompVersion),
         secretflow::spec::v1::ComponentDef(
             *teeapps::component::PearsonrComponent::GetInstance()
                  .Definition())},
        {GenCompFullName(kStatsDomain, kTableStatisticsComp, kCompVersion),
         secretflow::spec::v1::ComponentDef(
             *teeapps::component::TableStatisticsComponent::GetInstance()
                  .Definition())},
        {GenCompFullName(kStatsDomain, kVifComp, kCompVersion),
         secretflow::spec::v1::ComponentDef(
             *teeapps::component::VifComponent::GetInstance().Definition())},
        // Feature
        {GenCompFullName(kFeatureDomain, kVertWoeBinningComp, kCompVersion),
         secretflow::spec::v1::ComponentDef(
             *teeapps::component::WoeBinningComponent::GetInstance()
                  .Definition())},
        {GenCompFullName(kFeatureDomain, kVertWoeSubstitutionComp,
                         kCompVersion),
         secretflow::spec::v1::ComponentDef(
             *teeapps::component::WoeSubstitutionComponent::GetInstance()
                  .Definition())},
        // Ml
        {GenCompFullName(kMlEvalDomain, kBiclassificationEvalComp,
                         kCompVersion),
         secretflow::spec::v1::ComponentDef(
             *teeapps::component::BiclassificationComponent::GetInstance()
                  .Definition())},
        {GenCompFullName(kMlEvalDomain, kPredictionBiasComp, kCompVersion),
         secretflow::spec::v1::ComponentDef(
             *teeapps::component::PredictionBiasComponent::GetInstance()
                  .Definition())},
        {GenCompFullName(kMlPredictDomain, kXgbPredictComp, kCompVersion),
         secretflow::spec::v1::ComponentDef(
             *teeapps::component::XgbPredComponent::GetInstance()
                  .Definition())},
        {GenCompFullName(kMlPredictDomain, kLrPredictComp, kCompVersion),
         secretflow::spec::v1::ComponentDef(
             *teeapps::component::LrPredComponent::GetInstance().Definition())},
        {GenCompFullName(kMlTrainDomain, kXgbTrainComp, kCompVersion),
         secretflow::spec::v1::ComponentDef(
             *teeapps::component::XgbTrainComponent::GetInstance()
                  .Definition())},
        {GenCompFullName(kMlTrainDomain, kLrTrainComp, kCompVersion),
         secretflow::spec::v1::ComponentDef(
             *teeapps::component::LrTrainComponent::GetInstance()
                  .Definition())}};

}  // namespace framework
}  // namespace teeapps