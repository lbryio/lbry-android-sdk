# LBRY Android SDK
[![pipeline status](https://ci.lbry.tech/lbry/lbry-android-sdk/badges/master/pipeline.svg)](https://ci.lbry.tech/lbry/lbry-android-sdk/commits/master)
[![GitHub license](https://img.shields.io/github/license/lbryio/lbry-android-sdk)](https://github.com/lbryio/lbry-android/blob/master/LICENSE)

The LBRY SDK packaged as an Android AAR library which can be used in any Android Studio project.

## Installation
No installation required as this is a dev library.

## Usage
1. Open your project in Android Studio.
1. File > New > New Module...
1. Select Import .JAR / .AAR Package and click Next
1. Select the `lbrysdk-<version>-<debug|release>.aar` package from the location you built or downloaded it to where `version` is the sdk version and `<debug|release>` is either `debug` or `release`.
1. Click Finish
1. Add `implementation project(':lbrysdk-<version>-<debug|release>')` to the `build.gradle` configuration for the main app module.

### Using the SDK
Add the `FOREGROUND_SERVICE` and `INTERNET` permissions to `AndroidManifest.xml` if they are not yet added.
```
<uses-permission android:name="android.permission.FOREGROUND_SERVICE" />
<uses-permission android:name="android.permission.INTERNET" />
```
Add the `android:usesCleartextTraffic="true"` attribute to the `application` tag in `AndroidManifest.xml`.
Import the required classes to be able to start up the service.
```
import io.lbry.lbrysdk.LbrynetService;
import io.lbry.lbrysdk.ServiceHelper;
```
Add code to launch the service.
```
Context context = getApplicationContext();
ServiceHelper.start(context, "", LbrynetService.class, "lbrynetservice");
```


## Running from Source
The library can be built from source using [Buildozer](https://github.com/lbryio/buildozer). After cloning the repository, copy `buildozer.spec.sample` to `buildozer.spec` and modify this file as necessary for your environment. Please see [BUILD.md](BUILD.md) for detailed build instructions.

## Contributing
Contributions to this project are welcome, encouraged, and compensated. For more details, see https://lbry.io/faq/contributing

## License
This project is MIT licensed. For the full license, see [LICENSE](LICENSE).

## Security
We take security seriously. Please contact security@lbry.com regarding any security issues. Our PGP key is [here](https://keybase.io/lbry/key.asc) if you need it.

## Contact
The primary contact for this project is [@akinwale](https://github.com/akinwale) (akinwale@lbry.com)
