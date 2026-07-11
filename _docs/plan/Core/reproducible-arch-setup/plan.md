---
title: "Plan: Reproducible Arch setup"
status: active
draft_status: n/a
created_at: 2026-07-11
updated_at: 2026-07-11
references:
  - "_docs/intent/Core/reproducible-arch-setup/decision.md"
  - "_docs/qa/Core/reproducible-arch-setup/test-plan.md"
related_issues: []
related_prs: []
---

# Plan: Reproducible Arch setup

## Overview

Arch 系 Linux の中級者が、既存 Android SDK と Waydroid を用意した状態から、repo 内の説明と scripts だけで companion build、target-safe install、host bridge verification へ到達できるようにする。

## Scope

- host runtime と Android build に必要な Arch 系依存と成功判定を文書化する。
- SDK root を environment-first で解決し、一般配置を限定的に探索する。
- build tool / Java tool preflight と選択 version の表示を追加する。
- install / settings helpers に Waydroid auto-discovery と `--device` override を追加する。
- host unit / static checks を GitHub Actions で実行する。
- clean-room 相当の automated verification と、live Waydroid manual verification を分離する。

## Non-Goals

- Android SDK / Android Studio / JDK の自動導入。
- `sdkmanager --licenses` を含む license 自動受諾。
- Gradle migration、release signing、配布 APK、bit-for-bit reproducible build。
- Ubuntu / Fedora 等の非 Arch distro を検証済み対象にすること。
- CI 上で Waydroid / Apple Music live E2E を起動すること。

## Requirements

- **Functional**: `ANDROID_HOME` / `ANDROID_SDK_ROOT`、`$HOME/Android/Sdk`、`/opt/android-sdk`から SDK を決定し、platform / build-tools override を維持する。
- **Functional**: install / settings helpers は explicit target を優先し、自動検出不能時や非 ready target で別端末へ fallback しない。
- **Functional**: signature mismatch を destructive recovery せず、operator action を説明する。
- **Non-Functional**: source checkout と個人固有 path を分離し、failure message だけで不足前提を特定できる。
- **Non-Functional**: live environment を持たない CI でも target selection と host logic を regression-test できる。

## Tasks

1. SDK discovery / tool validation を独立 helper として実装し unit test する。
2. ADB target resolution を shell helpers から再利用可能な CLI boundary にする。
3. install / settings scripts の CLI、failure guidance、documentation を同期する。
4. GitHub Actions に host checks を追加する。
5. automated / manual verification evidence を記録する。

## QA Plan

- QA document: `_docs/qa/Core/reproducible-arch-setup/test-plan.md`
- Risk level: Medium
- Unit: SDK探索、tool選択、target precedence / fail-closed、signature mismatch guidance。
- Integration: build script、helper dry-run / fake command execution、existing host suite。
- Manual QA: live Waydroid build / install / settings / doctor。
- Validator / static check: Python compile、shell syntax、workflow review、docs validators、`git diff --check`。

## Deployment / Rollout

source-compatible script / docs update として main へ反映する。既存の environment overrides と live daemon behavior は維持する。問題時は旧 helpers へ戻せるが、生成済み APK、installed app、user service は自動変更・削除しない。
