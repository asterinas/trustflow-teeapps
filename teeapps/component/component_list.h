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

#include "absl/strings/str_cat.h"
#include "feature/woe_binning_component.h"
#include "feature/woe_substitution_component.h"
#include "ml/eval/biclassification_component.h"
#include "ml/eval/prediction_bias_component.h"
#include "ml/predict/lgbm_component.h"
#include "ml/predict/lr_component.h"
#include "ml/predict/xgb_component.h"
#include "ml/train/lgbm_component.h"
#include "ml/train/lr_component.h"
#include "ml/train/xgb_component.h"
#include "preprocessing/feature_filter_component.h"
#include "preprocessing/psi_component.h"
#include "preprocessing/train_test_split_component.h"
#include "stats/pearsonr_component.h"
#include "stats/table_statistics_component.h"
#include "stats/vif_component.h"

#include "secretflow/spec/v1/component.pb.h"

namespace teeapps {
namespace component {

// component domain
struct ComponentDomain {
  static constexpr char kPreProcessingDomain[] = "preprocessing";
  static constexpr char kStatsDomain[] = "stats";
  static constexpr char kMlEvalDomain[] = "ml.eval";
  static constexpr char kMlPredictDomain[] = "ml.predict";
  static constexpr char kMlTrainDomain[] = "ml.train";
  static constexpr char kFeatureDomain[] = "feature";
};

// component name
struct ComponentName {
  static constexpr char kPsiComp[] = "psi";
  static constexpr char kFeatureFilterComp[] = "feature_filter";
  static constexpr char kTrainTestSplitComp[] = "train_test_split";
  static constexpr char kPearsonrComp[] = "pearsonr";
  static constexpr char kVifComp[] = "vif";
  static constexpr char kTableStatisticsComp[] = "table_statistics";
  static constexpr char kWoeBinningComp[] = "woe_binning";
  static constexpr char kWoeSubstitutionComp[] = "woe_substitution";
  static constexpr char kXgbTrainComp[] = "xgb_train";
  static constexpr char kLrTrainComp[] = "lr_train";
  static constexpr char kLgbmTrainComp[] = "lgbm_train";
  static constexpr char kXgbPredictComp[] = "xgb_predict";
  static constexpr char kLrPredictComp[] = "lr_predict";
  static constexpr char kLgbmPredictComp[] = "lgbm_predict";
  static constexpr char kBiclassificationEvalComp[] = "biclassification_eval";
  static constexpr char kPredictionBiasComp[] = "prediction_bias_eval";
};

// component version
constexpr char kCompVersion[] = "0.0.1";

// python files of component implements
struct ComponentPyFile {
  static constexpr char kPsiPy[] = "psi.py";
  static constexpr char kFeatureFilterPy[] = "feature_filter.py";
  static constexpr char kTrainTestSplitPy[] = "train_test_split.py";
  static constexpr char kPearsonrPy[] = "pearsonr.py";
  static constexpr char kVifPy[] = "vif.py";
  static constexpr char kTableStatisticsPy[] = "table_statistics.py";
  static constexpr char kWoeBinningPy[] = "woe_binning.py";
  static constexpr char kWoeSubstitutionPy[] = "woe_substitution.py";
  static constexpr char kXgbPy[] = "xgb.py";
  static constexpr char kLrPy[] = "lr.py";
  static constexpr char kLgbmPy[] = "lgbm.py";
  static constexpr char kPredictPy[] = "predict.py";
  static constexpr char kBiclassEvalPy[] = "biclassification_eval.py";
  static constexpr char kPredBiasPy[] = "prediction_bias_eval.py";
};

const std::unordered_map<std::string, std::string> comp_py_map = {
    {ComponentName::kPsiComp, ComponentPyFile::kPsiPy},
    {ComponentName::kFeatureFilterComp, ComponentPyFile::kFeatureFilterPy},
    {ComponentName::kTrainTestSplitComp, ComponentPyFile::kTrainTestSplitPy},
    {ComponentName::kPearsonrComp, ComponentPyFile::kPearsonrPy},
    {ComponentName::kVifComp, ComponentPyFile::kVifPy},
    {ComponentName::kTableStatisticsComp, ComponentPyFile::kTableStatisticsPy},
    {ComponentName::kWoeBinningComp, ComponentPyFile::kWoeBinningPy},
    {ComponentName::kWoeSubstitutionComp, ComponentPyFile::kWoeSubstitutionPy},
    {ComponentName::kXgbTrainComp, ComponentPyFile::kXgbPy},
    {ComponentName::kLrTrainComp, ComponentPyFile::kLrPy},
    {ComponentName::kLgbmTrainComp, ComponentPyFile::kLgbmPy},
    {ComponentName::kXgbPredictComp, ComponentPyFile::kPredictPy},
    {ComponentName::kLrPredictComp, ComponentPyFile::kPredictPy},
    {ComponentName::kLgbmPredictComp, ComponentPyFile::kPredictPy},
    {ComponentName::kBiclassificationEvalComp, ComponentPyFile::kBiclassEvalPy},
    {ComponentName::kPredictionBiasComp, ComponentPyFile::kPredBiasPy}};

inline std::string GenCompFullName(const std::string& domain,
                                   const std::string& name,
                                   const std::string& version) {
  return absl::StrCat(domain, ".", name, ":", version);
}

const std::map<std::string, secretflow::spec::v1::ComponentDef> COMP_DEF_MAP = {
    // PreProcessing
    {GenCompFullName(ComponentDomain::kPreProcessingDomain,
                     ComponentName::kPsiComp, kCompVersion),
     secretflow::spec::v1::ComponentDef(
         *teeapps::component::PsiComponent::GetInstance().Definition())},
    {GenCompFullName(ComponentDomain::kPreProcessingDomain,
                     ComponentName::kFeatureFilterComp, kCompVersion),
     secretflow::spec::v1::ComponentDef(
         *teeapps::component::FeatureFilterComponent::GetInstance()
              .Definition())},
    {GenCompFullName(ComponentDomain::kPreProcessingDomain,
                     ComponentName::kTrainTestSplitComp, kCompVersion),
     secretflow::spec::v1::ComponentDef(
         *teeapps::component::TrainTestSplitComponent::GetInstance()
              .Definition())},
    // Stats
    {GenCompFullName(ComponentDomain::kStatsDomain,
                     ComponentName::kPearsonrComp, kCompVersion),
     secretflow::spec::v1::ComponentDef(
         *teeapps::component::PearsonrComponent::GetInstance().Definition())},
    {GenCompFullName(ComponentDomain::kStatsDomain,
                     ComponentName::kTableStatisticsComp, kCompVersion),
     secretflow::spec::v1::ComponentDef(
         *teeapps::component::TableStatisticsComponent::GetInstance()
              .Definition())},
    {GenCompFullName(ComponentDomain::kStatsDomain, ComponentName::kVifComp,
                     kCompVersion),
     secretflow::spec::v1::ComponentDef(
         *teeapps::component::VifComponent::GetInstance().Definition())},
    // Feature
    {GenCompFullName(ComponentDomain::kFeatureDomain,
                     ComponentName::kWoeBinningComp, kCompVersion),
     secretflow::spec::v1::ComponentDef(
         *teeapps::component::WoeBinningComponent::GetInstance().Definition())},
    {GenCompFullName(ComponentDomain::kFeatureDomain,
                     ComponentName::kWoeSubstitutionComp, kCompVersion),
     secretflow::spec::v1::ComponentDef(
         *teeapps::component::WoeSubstitutionComponent::GetInstance()
              .Definition())},
    // Ml
    {GenCompFullName(ComponentDomain::kMlTrainDomain,
                     ComponentName::kXgbTrainComp, kCompVersion),
     secretflow::spec::v1::ComponentDef(
         *teeapps::component::XgbTrainComponent::GetInstance().Definition())},
    {GenCompFullName(ComponentDomain::kMlTrainDomain,
                     ComponentName::kLrTrainComp, kCompVersion),
     secretflow::spec::v1::ComponentDef(
         *teeapps::component::LrTrainComponent::GetInstance().Definition())},
    {GenCompFullName(ComponentDomain::kMlTrainDomain,
                     ComponentName::kLgbmTrainComp, kCompVersion),
     secretflow::spec::v1::ComponentDef(
         *teeapps::component::LgbmTrainComponent::GetInstance().Definition())},
    {GenCompFullName(ComponentDomain::kMlPredictDomain,
                     ComponentName::kXgbPredictComp, kCompVersion),
     secretflow::spec::v1::ComponentDef(
         *teeapps::component::XgbPredComponent::GetInstance().Definition())},
    {GenCompFullName(ComponentDomain::kMlPredictDomain,
                     ComponentName::kLrPredictComp, kCompVersion),
     secretflow::spec::v1::ComponentDef(
         *teeapps::component::LrPredComponent::GetInstance().Definition())},
    {GenCompFullName(ComponentDomain::kMlPredictDomain,
                     ComponentName::kLgbmPredictComp, kCompVersion),
     secretflow::spec::v1::ComponentDef(
         *teeapps::component::LgbmPredComponent::GetInstance().Definition())},
    {GenCompFullName(ComponentDomain::kMlEvalDomain,
                     ComponentName::kBiclassificationEvalComp, kCompVersion),
     secretflow::spec::v1::ComponentDef(
         *teeapps::component::BiclassificationComponent::GetInstance()
              .Definition())},
    {GenCompFullName(ComponentDomain::kMlEvalDomain,
                     ComponentName::kPredictionBiasComp, kCompVersion),
     secretflow::spec::v1::ComponentDef(
         *teeapps::component::PredictionBiasComponent::GetInstance()
              .Definition())}};

}  // namespace component
}  // namespace teeapps