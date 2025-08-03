# Urdu Keyboard App

A beautiful, feature-rich Urdu-English keyboard app for Android with emoji support, color customization, and dual language capabilities.

## Features

- **Dual Language Support**: Switch seamlessly between Urdu and English
- **Complete Urdu Character Set**: All Urdu letters and diacritics included
- **Emoji Support**: Built-in emoji keyboard with popular emoticons
- **Color Customization**: Choose from predefined colors or create custom colors using RGB sliders
- **Beautiful UI**: Modern, sleek design with material design principles
- **Font Support**: 
  - Urdu text uses Noto Nastaliq Urdu font
  - English text uses Open Sans font
- **Settings**: Customizable vibration, sound, and color preferences
- **Persistent Settings**: Your color choices are saved automatically

## Installation

### Prerequisites
- Android Studio (latest version recommended)
- Android SDK API level 21 or higher
- Java 8 or higher

### Setup Instructions

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd UrduKeyboard
   ```

2. **Configure Android SDK:**
   - Open `local.properties` file
   - Set the path to your Android SDK:
     ```
     sdk.dir=/path/to/your/Android/Sdk
     ```

3. **Download required fonts:**
   The fonts should already be included, but if needed:
   - Open Sans: Available in `app/src/main/res/font/open_sans_regular.ttf`
   - Noto Nastaliq Urdu: Available in `app/src/main/res/font/nastaleq_regular.ttf`

4. **Download Gradle Wrapper JAR:**
   - Download `gradle-wrapper.jar` from [Gradle Releases](https://gradle.org/releases/)
   - Place it in `gradle/wrapper/gradle-wrapper.jar`

5. **Build the project:**
   ```bash
   ./gradlew assembleDebug
   ```

6. **Install on device:**
   ```bash
   ./gradlew installDebug
   ```

## Usage

### Setting up the keyboard:

1. **Install the app** on your Android device
2. **Open the app** and follow the setup instructions:
   - Tap "Open Settings" to enable the keyboard in system settings
   - Tap "Select" to set it as your default input method
3. **Customize the keyboard** by accessing Settings from the main app

### Using the keyboard:

- **Language Switch**: Tap the "اردو/Eng" button to switch between Urdu and English
- **Emoji Access**: Tap the emoji button (😀) to open emoji keyboard
- **Number Mode**: Tap "123" for numbers and symbols
- **Settings**: Long press the language button or access through the main app

## Color Customization

The keyboard offers extensive color customization:

1. **Predefined Colors**: Choose from 12 beautiful predefined colors
2. **Custom Colors**: Use RGB sliders to create any color you want
3. **Live Preview**: See your color changes in real-time
4. **Persistent Storage**: Your color choice is automatically saved

## Keyboard Layouts

### Urdu Layout
- Complete Urdu alphabet with proper Nastaliq font rendering
- Numbers row (0-9)
- Special Urdu characters and diacritics
- Space, Enter, Backspace, and Shift keys

### English Layout
- Standard QWERTY layout
- Uppercase/lowercase support with Shift key
- Numbers and symbols access

### Emoji Layout
- Popular smileys and emotions
- Hearts and hand gestures  
- Animals and nature emojis
- Easy access to space and backspace

## File Structure

```
app/
├── build.gradle                          # App-level Gradle configuration
├── proguard-rules.pro                    # ProGuard rules for code obfuscation
└── src/main/
    ├── AndroidManifest.xml               # App manifest with permissions and services
    ├── java/com/urdu/keyboard/
    │   ├── MainActivity.kt               # Main app activity
    │   ├── SettingsActivity.kt           # Settings and color customization
    │   └── UrduKeyboardService.kt        # Core keyboard input method service
    └── res/
        ├── drawable/                     # Key background drawables
        ├── font/                         # Urdu and English fonts
        ├── layout/                       # XML layouts for activities and keyboards
        ├── mipmap-*/                     # App icons for different densities
        ├── values/                       # Colors, strings, and themes
        └── xml/                          # Input method configuration
```

## Technical Details

### Architecture
- **Input Method Service**: Extends Android's `InputMethodService`
- **Custom Layouts**: XML-based keyboard layouts with programmatic key handling
- **Shared Preferences**: Settings persistence using Android's preference system
- **Material Design**: Modern UI following Material Design guidelines

### Key Components
- `UrduKeyboardService`: Main service handling keyboard input and display
- `MainActivity`: App launcher with keyboard setup instructions
- `SettingsActivity`: Color customization and preference management

### Fonts
- **Urdu**: Noto Nastaliq Urdu for authentic Urdu text rendering
- **English**: Open Sans for clean, readable English text

### Permissions
- `VIBRATE`: For haptic feedback on key press
- `ACCESS_NETWORK_STATE`: For potential future features

## Building for Release

1. **Generate signed APK:**
   ```bash
   ./gradlew assembleRelease
   ```

2. **The APK will be generated at:**
   ```
   app/build/outputs/apk/release/app-release.apk
   ```

## Troubleshooting

### Common Issues

1. **Keyboard not showing in settings:**
   - Ensure the app is properly installed
   - Check that `BIND_INPUT_METHOD` permission is correctly declared

2. **Fonts not displaying correctly:**
   - Verify font files are in the correct location
   - Check font file integrity

3. **Build errors:**
   - Ensure Android SDK path is correctly set in `local.properties`
   - Update Gradle wrapper if needed

4. **Color settings not saving:**
   - Check app has write permissions for shared preferences
   - Verify SharedPreferences implementation

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly on different devices
5. Submit a pull request

## License

This project is open source. Please see the LICENSE file for details.

## Support

For issues and feature requests, please create an issue in the repository.

## Acknowledgments

- Google Fonts for Noto Nastaliq Urdu and Open Sans fonts
- Android Open Source Project for input method framework
- Material Design for UI guidelines