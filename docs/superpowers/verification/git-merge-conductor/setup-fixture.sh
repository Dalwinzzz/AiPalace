#!/usr/bin/env bash
# setup-fixture.sh — build the toy repo used by all 5 verification scenarios.
# Per spec §14.1 of 2026-05-11-git-merge-conductor-design.md.
#
# Usage: ./setup-fixture.sh /tmp/merge-conductor-fixture
set -euo pipefail

DEST="${1:-/tmp/merge-conductor-fixture}"
rm -rf "$DEST"
mkdir -p "$DEST"
cd "$DEST"

git init -q -b main
git config user.email "fixture@local"
git config user.name "Fixture"

# Initial OrderService on main
mkdir -p src/service
cat > src/service/OrderService.java <<'JAVA'
package service;
import java.math.BigDecimal;
public class OrderService {
    private static final BigDecimal RATE = new BigDecimal("0.1");
    public BigDecimal calcDiscount(Order order) {
        BigDecimal base = order.getAmount().multiply(RATE);
        return base;
    }
}
JAVA
git add .
git commit -q -m "init: OrderService"

# Branch develop and release/v1.0 from main
git branch develop
git branch release/v1.0

# On release/v1.0: add VIP_BONUS feature
git checkout -q release/v1.0
cat > src/service/OrderService.java <<'JAVA'
package service;
import java.math.BigDecimal;
public class OrderService {
    private static final BigDecimal RATE = new BigDecimal("0.1");
    private static final BigDecimal VIP_BONUS = new BigDecimal("100");
    public BigDecimal calcDiscount(Order order) {
        BigDecimal base = order.getAmount().multiply(RATE);
        if (order.isVip()) {
            base = base.add(VIP_BONUS);
        }
        return base;
    }
}
JAVA
git add .
git commit -q -m "feat: add VIP_BONUS to calcDiscount"

# On develop: add coupon discount
git checkout -q develop
cat > src/service/OrderService.java <<'JAVA'
package service;
import java.math.BigDecimal;
public class OrderService {
    private static final BigDecimal RATE = new BigDecimal("0.1");
    private CouponService couponService;
    public BigDecimal calcDiscount(Order order) {
        BigDecimal base = order.getAmount().multiply(RATE);
        Coupon c = couponService.find(order.getUserId());
        if (c != null) base = base.subtract(c.value);
        return base;
    }
}
JAVA
git add .
git commit -q -m "feat: apply coupon to calcDiscount"

# Branch refactor/v2.0 from develop, rename calcDiscount → DiscountStrategy.apply
git checkout -q -b refactor/v2.0 develop
mkdir -p src/strategy
cat > src/strategy/DiscountStrategy.java <<'JAVA'
package strategy;
import java.math.BigDecimal;
public class DiscountStrategy {
    private static final BigDecimal RATE = new BigDecimal("0.1");
    private CouponService couponService;
    public BigDecimal apply(Order order) {
        BigDecimal base = order.getAmount().multiply(RATE);
        Coupon c = couponService.find(order.getUserId());
        if (c != null) base = base.subtract(c.value);
        return base;
    }
}
JAVA
git rm -q src/service/OrderService.java
git add .
git commit -q -m "refactor: rename OrderService.calcDiscount -> DiscountStrategy.apply"

# Branch feature/promo-v2 from develop~0 (current dev HEAD), simulating a feature
# branch that was based on develop AT THE TIME but predates the coupon feature.
# To simulate this properly, we branch from `develop~1` (BEFORE coupon was added).
git checkout -q -b feature/promo-v2 develop~1
cat > src/service/OrderService.java <<'JAVA'
package service;
import java.math.BigDecimal;
public class OrderService {
    private static final BigDecimal RATE = new BigDecimal("0.1");
    private static final BigDecimal VIP_BONUS = new BigDecimal("100");
    public BigDecimal calcDiscount(Order order) {
        BigDecimal base = order.getAmount().multiply(RATE);
        if (order.isVip()) {
            base = base.add(VIP_BONUS);
        }
        return base;
    }
}
JAVA
git add .
git commit -q -m "feat: VIP promo on feature branch"

# Back to develop as default landing point
git checkout -q develop

echo ""
echo "Fixture ready at $DEST"
echo ""
echo "Branches:"
git -C "$DEST" branch
echo ""
echo "Recent commits per branch (graph):"
git -C "$DEST" log --all --oneline --graph --decorate -15

# --- Scenario F: backport-transplant (care-class-to-develop) ---
# Simulates a target branch that has refactored since the source branch diverged.
# Source has 5 requirements; target has its own evolved logic on the same files.

rm -rf /tmp/gmc-fixture-F
mkdir -p /tmp/gmc-fixture-F
cd /tmp/gmc-fixture-F
git init -q
git config user.email "fixture@local"
git config user.name "Fixture"
git checkout -b base

# Initial common base — minimal Java-like file structure
mkdir -p src/main/java/com/example/course
cat > src/main/java/com/example/course/CourseOffline.java <<'JAVA'
package com.example.course;

public class CourseOffline {
    public String getDisplayName() {
        return "default";
    }
}
JAVA

cat > pom.xml <<'XML'
<project>
  <modelVersion>4.0.0</modelVersion>
  <groupId>com.example</groupId>
  <artifactId>care-class</artifactId>
  <version>1.0</version>
  <packaging>jar</packaging>
  <build>
    <finalName>care-class</finalName>
    <plugins>
      <plugin>
        <groupId>org.apache.maven.plugins</groupId>
        <artifactId>maven-compiler-plugin</artifactId>
        <version>3.8.1</version>
        <configuration><source>1.8</source><target>1.8</target></configuration>
      </plugin>
    </plugins>
  </build>
</project>
XML
git add . && git commit -q -m "base: minimal CourseOffline + pom"

# Target branch (develop) — has evolved with project-aware logic but DIFFERENT shape than source
git checkout -b develop
cat > src/main/java/com/example/course/CourseOffline.java <<'JAVA'
package com.example.course;

import java.util.List;

public class CourseOffline {
    private List<Teacher> teacherList;

    public String getDisplayName() {
        if (teacherList != null && !teacherList.isEmpty()) {
            return teacherList.get(0).getName();
        }
        return "default";
    }

    public String getRegionalName(String project) {
        // Hangzhou & Nanjing iteration added in develop after merge-base
        if ("HANGZHOU".equals(project)) return "杭州-" + getDisplayName();
        if ("NANJING".equals(project)) return "南京-" + getDisplayName();
        return getDisplayName();
    }
}
JAVA
cat > src/main/java/com/example/course/Teacher.java <<'JAVA'
package com.example.course;
public class Teacher {
    private String name;
    public String getName() { return name; }
    public void setName(String n) { this.name = n; }
}
JAVA
git add . && git commit -q -m "develop: evolve to teacherList + regional name (HZ/NJ)"

# Source branch (refactor/micro-core-dev) — diverged with care-class plugin structure
git checkout base
git checkout -b refactor/micro-core-dev
mkdir -p plugins/care-class/src/main/java/com/example/care
cat > plugins/care-class/src/main/java/com/example/care/CareClassUtil.java <<'JAVA'
package com.example.care;
// Source's care-class-specific implementation, plugin-isolated
public class CareClassUtil {
    public static String normalizeCareClassTeacherName(String project, String raw) {
        // Source's logic uses projectName guard — this is what care-class round-3 had to FIX
        if ("JIASHAN".equals(project)) {
            return raw.replace("老师", "");
        }
        return raw;
    }
}
JAVA
# Source also has CourseOffline override
cat > src/main/java/com/example/course/CourseOffline.java <<'JAVA'
package com.example.course;
// Source's diverged CourseOffline — does NOT have teacherList; uses raw string
public class CourseOffline {
    private String careClassTeacher;

    public String getDisplayName() {
        if (careClassTeacher != null) {
            // direct call into plugin
            return com.example.care.CareClassUtil.normalizeCareClassTeacherName("JIASHAN", careClassTeacher);
        }
        return "default";
    }
}
JAVA
git add . && git commit -q -m "refactor/micro-core-dev: plugin-style CareClassUtil + CourseOffline override"

echo "Scenario F fixture ready at /tmp/gmc-fixture-F. Source: refactor/micro-core-dev. Target: develop."
