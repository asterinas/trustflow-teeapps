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

#include "../component.h"

namespace teeapps {
namespace component {

class TableStatisticsComponent : public Component {
 public:
  void Init();

  explicit TableStatisticsComponent(
      const std::string& name = "table_statistics",
      const std::string& domain = "stats", const std::string& version = "0.0.1",
      const std::string& desc =
          "Get a table of statistics,\nincluding each column's\n1. "
          "datatype\n2. total_count\n3. count\n4. count_na\n5. na_ratio\n6. "
          "min\n7. max\n8. mean\n9. var\n10. std\n11. sem\n12. skewness\n13. "
          "kurtosis\n14. q1\n15. q2\n16. q3\n17. moment_2\n18. moment_3\n19. "
          "moment_4\n20. central_moment_2\n21. central_moment_3\n22. "
          "central_moment_4\n23. sum\n24. sum_2\n25. sum_3\n26. sum_4\n- "
          "moment_2 means E[X^2].\n- central_moment_2 means E[(X - "
          "mean(X))^2].\n- sum_2 means sum(X^2).")
      : Component(name, domain, version, desc) {
    Init();
  }
  ~TableStatisticsComponent() {}
  TableStatisticsComponent(const TableStatisticsComponent&) = delete;
  const TableStatisticsComponent& operator=(const TableStatisticsComponent&) =
      delete;

 public:
  static TableStatisticsComponent& GetInstance() {
    static TableStatisticsComponent instance;
    return instance;
  }
};

}  // namespace component
}  // namespace teeapps
