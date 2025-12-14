plugins {
    alias(libs.plugins.android.application)
    alias(libs.plugins.kotlin.android)
}

// Функция для чтения версии из main.py
fun readVersionFromPython(): String {
    val mainPyFile = file("${rootProject.projectDir}/python/main.py")
    if (!mainPyFile.exists()) {
        println("Warning: python/main.py not found, using default version")
        return "0.6.0"
    }
    
    val versionPattern = Regex("""version\s*=\s*["']([\d.]+)["']""")
    val content = mainPyFile.readText()
    
    val matchResult = versionPattern.find(content)
    if (matchResult != null) {
        val version = matchResult.groupValues[1]
        println("Found version in main.py: $version")
        return version
    }
    
    println("Warning: Could not find version in main.py, using default version")
    return "0.6.0"
}

android {
    namespace = "com.example.test"
    compileSdk = 36

    defaultConfig {
        applicationId = "com.example.test"
        minSdk = 24
        targetSdk = 35
        versionCode = 1
        versionName = readVersionFromPython()

        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
    }

    buildTypes {
        release {
            isMinifyEnabled = false
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro"
            )
            signingConfig = signingConfigs.getByName("debug")
        }
    }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_11
        targetCompatibility = JavaVersion.VERSION_11
    }
    kotlinOptions {
        jvmTarget = "11"
    }
    
    // Настройки кодировки для Java компиляции
    tasks.withType<JavaCompile>().configureEach {
        options.encoding = "UTF-8"
    }
}

dependencies {

    implementation(libs.androidx.core.ktx)
    implementation(libs.androidx.appcompat)
    implementation(libs.material)
    implementation(libs.androidx.activity)
    implementation(libs.androidx.constraintlayout)
    implementation(libs.activity)
    implementation(libs.appcompat)
    testImplementation(libs.junit)
    androidTestImplementation(libs.androidx.junit)
    androidTestImplementation(libs.androidx.espresso.core)
    implementation ("com.squareup.retrofit2:retrofit:2.9.0")
    implementation ("com.squareup.retrofit2:converter-gson:2.9.0")
    implementation ("com.squareup.okhttp3:logging-interceptor:4.11.0")
    implementation ("com.google.code.gson:gson:2.10.1")
    implementation ("com.github.bumptech.glide:glide:4.16.0")
    annotationProcessor ("com.github.bumptech.glide:compiler:4.16.0")
    implementation ("androidx.cardview:cardview:1.0.0")
    
    // Lifecycle для ViewModel и LiveData
    implementation ("androidx.lifecycle:lifecycle-runtime-ktx:2.7.0")
    implementation ("androidx.lifecycle:lifecycle-livedata-ktx:2.7.0")
    implementation ("androidx.lifecycle:lifecycle-viewmodel-ktx:2.7.0")
    
    // RecyclerView
    implementation ("androidx.recyclerview:recyclerview:1.3.2")
    
    // CoordinatorLayout
    implementation ("androidx.coordinatorlayout:coordinatorlayout:1.2.0")
}

// Create testClasses task for compatibility with standard Gradle projects
// This task compiles test classes without running them
afterEvaluate {
    tasks.register("testClasses") {
        description = "Assembles test classes"
        group = "verification"
        
        // Depend on all test compilation tasks
        val testCompileTasks = tasks.matching { task ->
            task.name.startsWith("compile") && 
            (task.name.contains("UnitTest") || task.name.contains("AndroidTest"))
        }
        dependsOn(testCompileTasks)
    }
}