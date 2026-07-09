#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROBE_DIR="$ROOT_DIR/android/probe"
BUILD_DIR="$PROBE_DIR/build"
SDK_ROOT="${ANDROID_HOME:-${ANDROID_SDK_ROOT:-/home/penne/Android/Sdk}}"

if [[ ! -d "$SDK_ROOT" ]]; then
  echo "Android SDK not found: $SDK_ROOT" >&2
  exit 1
fi

latest_child() {
  find "$1" -mindepth 1 -maxdepth 1 -type d -printf '%f\n' | sort -V | tail -n 1
}

PLATFORM_NAME="${ANDROID_PLATFORM:-$(latest_child "$SDK_ROOT/platforms")}"
BUILD_TOOLS_NAME="${ANDROID_BUILD_TOOLS:-$(latest_child "$SDK_ROOT/build-tools")}"

ANDROID_JAR="$SDK_ROOT/platforms/$PLATFORM_NAME/android.jar"
BUILD_TOOLS="$SDK_ROOT/build-tools/$BUILD_TOOLS_NAME"
AAPT2="$BUILD_TOOLS/aapt2"
D8="$BUILD_TOOLS/d8"
ZIPALIGN="$BUILD_TOOLS/zipalign"
APKSIGNER="$BUILD_TOOLS/apksigner"

for tool in "$ANDROID_JAR" "$AAPT2" "$D8" "$ZIPALIGN" "$APKSIGNER"; do
  if [[ ! -e "$tool" ]]; then
    echo "Required Android build tool missing: $tool" >&2
    exit 1
  fi
done

rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR"/{classes,dex,generated,outputs}

COMPILED_RES="$BUILD_DIR/compiled_res.zip"
RES_APK="$BUILD_DIR/probe-res.apk"
UNSIGNED_APK="$BUILD_DIR/probe-unsigned.apk"
ALIGNED_APK="$BUILD_DIR/probe-aligned.apk"
OUTPUT_APK="$BUILD_DIR/outputs/waydroid-mpris-probe-debug.apk"
KEYSTORE="$PROBE_DIR/debug.keystore"

"$AAPT2" compile --dir "$PROBE_DIR/src/main/res" -o "$COMPILED_RES"
"$AAPT2" link \
  -I "$ANDROID_JAR" \
  --manifest "$PROBE_DIR/src/main/AndroidManifest.xml" \
  --java "$BUILD_DIR/generated" \
  -o "$RES_APK" \
  "$COMPILED_RES"

mapfile -t JAVA_SOURCES < <(find "$PROBE_DIR/src/main/java" "$BUILD_DIR/generated" -name '*.java' | sort)
javac \
  -source 8 \
  -target 8 \
  -bootclasspath "$ANDROID_JAR" \
  -classpath "$BUILD_DIR/generated" \
  -d "$BUILD_DIR/classes" \
  "${JAVA_SOURCES[@]}"

CLASSES_JAR="$BUILD_DIR/classes.jar"
(cd "$BUILD_DIR/classes" && jar cf "$CLASSES_JAR" .)
"$D8" --lib "$ANDROID_JAR" --output "$BUILD_DIR/dex" "$CLASSES_JAR"
cp "$RES_APK" "$UNSIGNED_APK"
(cd "$BUILD_DIR/dex" && jar uf "$UNSIGNED_APK" classes.dex)

if [[ ! -f "$KEYSTORE" ]]; then
  keytool -genkeypair \
    -keystore "$KEYSTORE" \
    -storepass android \
    -keypass android \
    -alias androiddebugkey \
    -keyalg RSA \
    -keysize 2048 \
    -validity 10000 \
    -dname "CN=Android Debug,O=Android,C=US" >/dev/null
fi

"$ZIPALIGN" -f -p 4 "$UNSIGNED_APK" "$ALIGNED_APK"
"$APKSIGNER" sign \
  --ks "$KEYSTORE" \
  --ks-pass pass:android \
  --key-pass pass:android \
  --out "$OUTPUT_APK" \
  "$ALIGNED_APK"
"$APKSIGNER" verify "$OUTPUT_APK"

echo "$OUTPUT_APK"
