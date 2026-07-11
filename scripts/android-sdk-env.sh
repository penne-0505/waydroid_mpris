#!/usr/bin/env bash

android_sdk_die() {
  echo "error: $*" >&2
  return 1
}

android_sdk_latest_child() {
  local parent="$1"
  [[ -d "$parent" ]] || return 1
  find "$parent" -mindepth 1 -maxdepth 1 -type d -printf '%f\n' | sort -V | tail -n 1
}

resolve_android_sdk() {
  local sdk_root=""
  local candidate=""

  # intent: INV-002 (Core/reproducible-arch-setup) — an explicit SDK root must not be hidden by a machine-local fallback.
  if [[ -n "${ANDROID_HOME:-}" ]]; then
    sdk_root="$ANDROID_HOME"
  elif [[ -n "${ANDROID_SDK_ROOT:-}" ]]; then
    sdk_root="$ANDROID_SDK_ROOT"
  else
    for candidate in "${HOME:-}/Android/Sdk" /opt/android-sdk; do
      if [[ -n "$candidate" && -d "$candidate" ]]; then
        sdk_root="$candidate"
        break
      fi
    done
  fi

  if [[ -z "$sdk_root" || ! -d "$sdk_root" ]]; then
    android_sdk_die "Android SDK not found. Set ANDROID_HOME or ANDROID_SDK_ROOT to an existing SDK root."
    return 1
  fi

  local platform_name="${ANDROID_PLATFORM:-}"
  local build_tools_name="${ANDROID_BUILD_TOOLS:-}"
  if [[ -z "$platform_name" ]]; then
    platform_name="$(android_sdk_latest_child "$sdk_root/platforms")"
  fi
  if [[ -z "$build_tools_name" ]]; then
    build_tools_name="$(android_sdk_latest_child "$sdk_root/build-tools")"
  fi
  if [[ -z "$platform_name" ]]; then
    android_sdk_die "no Android SDK platform found under $sdk_root/platforms"
    return 1
  fi
  if [[ -z "$build_tools_name" ]]; then
    android_sdk_die "no Android SDK Build-Tools found under $sdk_root/build-tools"
    return 1
  fi

  for command_name in javac jar keytool; do
    command -v "$command_name" >/dev/null 2>&1 || {
      android_sdk_die "required JDK command not found in PATH: $command_name"
      return 1
    }
  done

  SDK_ROOT="$sdk_root"
  PLATFORM_NAME="$platform_name"
  BUILD_TOOLS_NAME="$build_tools_name"
  ANDROID_JAR="$SDK_ROOT/platforms/$PLATFORM_NAME/android.jar"
  BUILD_TOOLS="$SDK_ROOT/build-tools/$BUILD_TOOLS_NAME"
  AAPT2="$BUILD_TOOLS/aapt2"
  D8="$BUILD_TOOLS/d8"
  ZIPALIGN="$BUILD_TOOLS/zipalign"
  APKSIGNER="$BUILD_TOOLS/apksigner"

  local required_path
  for required_path in "$ANDROID_JAR" "$AAPT2" "$D8" "$ZIPALIGN" "$APKSIGNER"; do
    if [[ ! -e "$required_path" ]]; then
      android_sdk_die "required Android SDK component missing: $required_path"
      return 1
    fi
  done

  echo "Android SDK: $SDK_ROOT" >&2
  echo "Android platform: $PLATFORM_NAME" >&2
  echo "Android Build-Tools: $BUILD_TOOLS_NAME" >&2
}
