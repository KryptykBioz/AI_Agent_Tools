# Unity VRM Avatar Control with Ollama LLM - Complete Setup Guide

## Overview
This guide will walk you through setting up a system where a local Ollama LLM can control VRM avatars in Unity using keyword-triggered animations, similar to Warudo's functionality.

## Prerequisites
- Unity 2022.3 LTS or newer
- VRM models already imported in Unity
- Ollama installed locally
- Basic C# programming knowledge
- Understanding of Unity's Animation system

## Part 1: Setting Up VRM in Unity

### 1.1 Install Required Packages
1. Open Unity Package Manager (Window → Package Manager)
2. Install these packages:
   - **UniVRM** (for VRM support)
   - **Newtonsoft Json** (for JSON parsing)
   - **WebGL Networking** (if targeting WebGL)

### 1.2 Verify VRM Import
1. Ensure your VRM models are properly imported
2. Check that animations are correctly assigned to the Animator Controller
3. Verify that the VRM components are attached to your avatar GameObjects

## Part 2: Animation System Setup

### 2.1 Create Animation Controller
1. Right-click in Project window → Create → Animator Controller
2. Name it `VRMAvatarController`
3. Open the Animator window (Window → Animation → Animator)

### 2.2 Set Up Animation States

#### Step-by-Step State Creation:
1. **Open your Animator Controller** in the Animator window
2. **Delete the default states** if present (right-click → Delete)
3. **Create the main states:**

   **For each animation, follow these steps:**
   
   a) **Right-click in empty area** → Create State → Empty
   
   b) **Name the state** (e.g., "Idle", "Happy", "Wave", etc.)
   
   c) **Assign the animation clip:**
      - Select the state
      - In Inspector, find "Motion" field
      - Drag your VRM animation clip from Project window
      - Or click the circle icon to browse and select
   
   d) **Create these specific states:**
      - **Idle** (set as default - right-click → Set as Layer Default State)
      - **Happy** 
      - **Sad**
      - **Wave**
      - **Dance**
      - **Bow** 
      - **Think**
      - **Surprised**
      - **Angry**
      - **Confused**

#### State Configuration:
- **Idle State**: Set "Write Defaults" to ON, Speed = 1.0
- **All Other States**: Set "Write Defaults" to OFF, Speed = 1.0
- **Loop animations** where appropriate (check "Loop Time" in animation import settings)

### 2.3 Add Parameters and Transitions

#### 2.3.1 Adding Parameters (CORRECTED):
**Unity doesn't have a "String" parameter type.** Here's the correct approach:

1. **Click the "+" button** in Parameters tab
2. **Add these parameters:**
   - `ToIdle` (Bool type) - for returning to idle
   - `ToHappy` (Bool type) - for happy animation
   - `ToSad` (Bool type) - for sad animation  
   - `ToWave` (Bool type) - for wave animation
   - `ToDance` (Bool type) - for dance animation
   - `ToBow` (Bool type) - for bow animation
   - `ToThink` (Bool type) - for think animation
   - `ToSurprised` (Bool type) - for surprised animation
   - `ToAngry` (Bool type) - for angry animation
   - `ToConfused` (Bool type) - for confused animation

#### 2.3.2 Alternative Approach (Recommended):
Instead of multiple bools, use **Integer parameters** for cleaner management:

1. **Add these parameters:**
   - `AnimationIndex` (Int type, default value = 0)
   - `TriggerAnimation` (Trigger type)

2. **Animation Index Values:**
   - 0 = Idle
   - 1 = Happy
   - 2 = Sad
   - 3 = Wave
   - 4 = Dance
   - 5 = Bow
   - 6 = Think
   - 7 = Surprised
   - 8 = Angry
   - 9 = Confused

#### 2.3.3 Creating Transitions:

**From Any State to Specific Animations:**
1. **Right-click on "Any State"** → Make Transition
2. **Drag the arrow** to your target state (e.g., Happy)
3. **Select the transition arrow**
4. **In Inspector, set conditions:**
   - Condition: `AnimationIndex` Equals `1` (for Happy)
   - AND `TriggerAnimation` (trigger condition)
5. **Uncheck "Has Exit Time"**
6. **Set "Transition Duration"** to 0.1-0.25 for smooth transitions

**Repeat for all animation states.**

**From Animation States back to Idle:**
1. **Select each animation state** (Happy, Sad, etc.)
2. **Right-click → Make Transition** → drag to Idle
3. **Set transition conditions:**
   - Condition: `AnimationIndex` Equals `0`
   - OR use "Has Exit Time" checked with appropriate duration
4. **Set "Transition Duration"** to 0.25

#### 2.3.4 Advanced Transition Setup:

**For automatic return to Idle after animation:**
1. **On each animation state** (not Idle):
   - **Check "Has Exit Time"** 
   - **Set "Exit Time"** to 0.95 (95% through animation)
   - **Transition Duration** = 0.25
   - **Target**: Idle state
   - **No conditions needed** (automatic)

**For immediate animation switching:**
1. **From Any State transitions:**
   - **Uncheck "Has Exit Time"**
   - **Set "Transition Duration"** to 0.1
   - **Check "Can Transition To Self"** if needed

#### 2.3.5 Visual Animator Layout:
```
[Any State] ──┐
              ├──→ [Idle] (Default)
              ├──→ [Happy]
              ├──→ [Sad]  
              ├──→ [Wave]
              ├──→ [Dance]
              ├──→ [Bow]
              ├──→ [Think]
              ├──→ [Surprised]
              ├──→ [Angry]
              └──→ [Confused]

Each animation state has:
- Transition FROM Any State (with conditions)
- Transition TO Idle (automatic after duration)
```

#### 2.3.6 Testing Your Setup:
1. **Play the scene**
2. **In Animator window**, you should see:
   - Current state highlighted in blue
   - Parameter values updating in real-time
3. **Test by manually changing parameters:**
   - Set `AnimationIndex` to different values (1-9)
   - Click the `TriggerAnimation` trigger
4. **Verify transitions work smoothly**

#### 2.3.7 Troubleshooting Animation Setup:
- **Animations not playing**: Check that Motion field has correct animation clips assigned
- **Stuck in transition**: Verify "Has Exit Time" settings and Exit Time values
- **Parameters not working**: Ensure parameter names match exactly in script and Animator
- **Immediate switching issues**: Adjust "Transition Duration" and "Interruption Source" settings

## Part 3: Unity Scripts Implementation

### 3.1 Create the Animation Controller Script

```csharp
using UnityEngine;
using System.Collections.Generic;

public class VRMAnimationController : MonoBehaviour
{
    [Header("Animation Settings")]
    public Animator animator;
    public float animationDuration = 3f;
    public bool autoReturnToIdle = true;
    
    [Header("Available Animations")]
    public List<string> availableAnimations = new List<string>
    {
        "idle", "happy", "sad", "wave", "dance", "bow", 
        "think", "surprised", "angry", "confused"
    };
    
    private Dictionary<string, string> animationAliases;
    private Dictionary<string, int> animationIndices;
    private Coroutine currentAnimationCoroutine;
    
    void Start()
    {
        if (animator == null)
            animator = GetComponent<Animator>();
            
        InitializeAnimationMappings();
    }
    
    void InitializeAnimationMappings()
    {
        // Animation aliases for natural language
        animationAliases = new Dictionary<string, string>
        {
            // Emotion keywords
            {"joy", "happy"}, {"happiness", "happy"}, {"excited", "happy"},
            {"sadness", "sad"}, {"cry", "sad"}, {"upset", "sad"},
            {"hello", "wave"}, {"hi", "wave"}, {"goodbye", "wave"},
            {"dancing", "dance"}, {"party", "dance"},
            {"greeting", "bow"}, {"respect", "bow"}, {"thank", "bow"},
            {"thinking", "think"}, {"wonder", "think"}, {"ponder", "think"},
            {"shock", "surprised"}, {"wow", "surprised"}, {"amazed", "surprised"},
            {"mad", "angry"}, {"furious", "angry"}, {"rage", "angry"},
            {"puzzled", "confused"}, {"what", "confused"}, {"huh", "confused"}
        };
        
        // Animation name to index mapping (matches Animator Controller setup)
        animationIndices = new Dictionary<string, int>
        {
            {"idle", 0}, {"happy", 1}, {"sad", 2}, {"wave", 3}, 
            {"dance", 4}, {"bow", 5}, {"think", 6}, {"surprised", 7}, 
            {"angry", 8}, {"confused", 9}
        };
    }
    
    public void TriggerAnimation(string keyword)
    {
        string animationName = ResolveAnimationName(keyword.ToLower());
        
        if (string.IsNullOrEmpty(animationName))
        {
            Debug.LogWarning($"Animation keyword '{keyword}' not recognized");
            return;
        }
        
        PlayAnimation(animationName);
    }
    
    string ResolveAnimationName(string keyword)
    {
        // Direct match
        if (availableAnimations.Contains(keyword))
            return keyword;
            
        // Alias match
        if (animationAliases.ContainsKey(keyword))
            return animationAliases[keyword];
            
        return null;
    }
    
    void PlayAnimation(string animationName)
    {
        if (currentAnimationCoroutine != null)
            StopCoroutine(currentAnimationCoroutine);
        
        // Get animation index
        if (animationIndices.ContainsKey(animationName))
        {
            int animIndex = animationIndices[animationName];
            
            // Set animator parameters
            animator.SetInteger("AnimationIndex", animIndex);
            animator.SetTrigger("TriggerAnimation");
            
            Debug.Log($"Playing animation: {animationName} (Index: {animIndex})");
            
            if (autoReturnToIdle && animationName != "idle")
            {
                currentAnimationCoroutine = StartCoroutine(ReturnToIdleAfterDelay());
            }
        }
        else
        {
            Debug.LogError($"Animation '{animationName}' not found in animation indices!");
        }
    }
    
    System.Collections.IEnumerator ReturnToIdleAfterDelay()
    {
        yield return new WaitForSeconds(animationDuration);
        
        // Return to idle
        animator.SetInteger("AnimationIndex", 0);
        animator.SetTrigger("TriggerAnimation");
        
        Debug.Log("Returned to idle animation");
    }
    
    public void SetAnimationDuration(float duration)
    {
        animationDuration = duration;
    }
    
    // Manual testing methods (can be called from buttons in inspector)
    [System.Obsolete("Use TriggerAnimation instead")]
    public void TestHappy() { TriggerAnimation("happy"); }
    [System.Obsolete("Use TriggerAnimation instead")]
    public void TestSad() { TriggerAnimation("sad"); }
    [System.Obsolete("Use TriggerAnimation instead")]
    public void TestWave() { TriggerAnimation("wave"); }
}
```

### 3.2 Create the Ollama Communication Script

```csharp
using UnityEngine;
using UnityEngine.Networking;
using System.Collections;
using System.Text;
using Newtonsoft.Json;
using System.Text.RegularExpressions;

public class OllamaController : MonoBehaviour
{
    [Header("Ollama Settings")]
    public string ollamaUrl = "http://localhost:11434";
    public string modelName = "llama2";
    public int maxTokens = 150;
    
    [Header("Avatar Control")]
    public VRMAnimationController avatarController;
    public float responseInterval = 5f;
    
    [Header("Conversation")]
    public string systemPrompt = "You are controlling a VRM avatar. Respond naturally to conversations and include animation keywords in brackets like [happy], [wave], [think]. Available animations: idle, happy, sad, wave, dance, bow, think, surprised, angry, confused.";
    
    private bool isProcessing = false;
    
    [System.Serializable]
    public class OllamaRequest
    {
        public string model;
        public string prompt;
        public bool stream = false;
        public OllamaOptions options;
    }
    
    [System.Serializable]
    public class OllamaOptions
    {
        public int num_predict;
        public float temperature = 0.7f;
    }
    
    [System.Serializable]
    public class OllamaResponse
    {
        public string response;
        public bool done;
    }
    
    void Start()
    {
        if (avatarController == null)
            avatarController = FindObjectOfType<VRMAnimationController>();
    }
    
    public void SendMessageToOllama(string userMessage)
    {
        if (isProcessing)
        {
            Debug.Log("Already processing a request...");
            return;
        }
        
        StartCoroutine(ProcessOllamaRequest(userMessage));
    }
    
    IEnumerator ProcessOllamaRequest(string userMessage)
    {
        isProcessing = true;
        
        string fullPrompt = $"{systemPrompt}\n\nUser: {userMessage}\nAssistant:";
        
        OllamaRequest request = new OllamaRequest
        {
            model = modelName,
            prompt = fullPrompt,
            options = new OllamaOptions
            {
                num_predict = maxTokens
            }
        };
        
        string jsonRequest = JsonConvert.SerializeObject(request);
        
        using (UnityWebRequest www = new UnityWebRequest($"{ollamaUrl}/api/generate", "POST"))
        {
            byte[] bodyRaw = Encoding.UTF8.GetBytes(jsonRequest);
            www.uploadHandler = new UploadHandlerRaw(bodyRaw);
            www.downloadHandler = new DownloadHandlerBuffer();
            www.SetRequestHeader("Content-Type", "application/json");
            
            yield return www.SendWebRequest();
            
            if (www.result != UnityWebRequest.Result.Success)
            {
                Debug.LogError($"Ollama request failed: {www.error}");
                isProcessing = false;
                yield break;
            }
            
            try
            {
                OllamaResponse response = JsonConvert.DeserializeObject<OllamaResponse>(www.downloadHandler.text);
                ProcessResponse(response.response);
            }
            catch (System.Exception e)
            {
                Debug.LogError($"Failed to parse Ollama response: {e.Message}");
            }
        }
        
        isProcessing = false;
    }
    
    void ProcessResponse(string response)
    {
        Debug.Log($"Ollama Response: {response}");
        
        // Extract animation keywords from brackets [keyword]
        MatchCollection matches = Regex.Matches(response, @"\[(\w+)\]");
        
        foreach (Match match in matches)
        {
            string animationKeyword = match.Groups[1].Value;
            avatarController.TriggerAnimation(animationKeyword);
            
            // Add delay between multiple animations
            if (matches.Count > 1)
            {
                StartCoroutine(DelayedAnimation(animationKeyword, 0.5f));
            }
        }
        
        // If no specific animation found, analyze sentiment
        if (matches.Count == 0)
        {
            AnalyzeSentimentAndAnimate(response);
        }
    }
    
    IEnumerator DelayedAnimation(string keyword, float delay)
    {
        yield return new WaitForSeconds(delay);
        avatarController.TriggerAnimation(keyword);
    }
    
    void AnalyzeSentimentAndAnimate(string text)
    {
        string lowerText = text.ToLower();
        
        if (lowerText.Contains("happy") || lowerText.Contains("great") || lowerText.Contains("wonderful"))
            avatarController.TriggerAnimation("happy");
        else if (lowerText.Contains("sad") || lowerText.Contains("sorry") || lowerText.Contains("unfortunately"))
            avatarController.TriggerAnimation("sad");
        else if (lowerText.Contains("?") || lowerText.Contains("think") || lowerText.Contains("consider"))
            avatarController.TriggerAnimation("think");
        else if (lowerText.Contains("!") || lowerText.Contains("wow") || lowerText.Contains("amazing"))
            avatarController.TriggerAnimation("surprised");
        else
            avatarController.TriggerAnimation("idle");
    }
    
    // Public method for UI integration
    public void OnUserInput(string input)
    {
        if (!string.IsNullOrEmpty(input))
        {
            SendMessageToOllama(input);
        }
    }
}
```

### 3.3 Create UI Input Handler

```csharp
using UnityEngine;
using UnityEngine.UI;

public class ChatUI : MonoBehaviour
{
    [Header("UI Elements")]
    public InputField inputField;
    public Button sendButton;
    public Text chatDisplay;
    public ScrollRect scrollRect;
    
    [Header("Controllers")]
    public OllamaController ollamaController;
    
    private string chatHistory = "";
    
    void Start()
    {
        if (sendButton != null)
            sendButton.onClick.AddListener(OnSendButtonClicked);
            
        if (inputField != null)
            inputField.onEndEdit.AddListener(OnInputEndEdit);
    }
    
    void OnSendButtonClicked()
    {
        SendMessage();
    }
    
    void OnInputEndEdit(string input)
    {
        if (Input.GetKeyDown(KeyCode.Return) || Input.GetKeyDown(KeyCode.KeypadEnter))
        {
            SendMessage();
        }
    }
    
    void SendMessage()
    {
        if (inputField == null || string.IsNullOrEmpty(inputField.text.Trim()))
            return;
            
        string userMessage = inputField.text.Trim();
        
        // Update chat display
        chatHistory += $"\nUser: {userMessage}";
        UpdateChatDisplay();
        
        // Send to Ollama
        ollamaController.OnUserInput(userMessage);
        
        // Clear input
        inputField.text = "";
        inputField.ActivateInputField();
    }
    
    void UpdateChatDisplay()
    {
        if (chatDisplay != null)
        {
            chatDisplay.text = chatHistory;
            
            // Auto-scroll to bottom
            if (scrollRect != null)
            {
                Canvas.ForceUpdateCanvases();
                scrollRect.verticalNormalizedPosition = 0f;
            }
        }
    }
    
    public void AddAIResponse(string response)
    {
        chatHistory += $"\nAI: {response}";
        UpdateChatDisplay();
    }
}
```

## Part 4: Ollama Setup and Configuration

### 4.1 Install and Configure Ollama
1. Download and install Ollama from [ollama.ai](https://ollama.ai)
2. Open terminal/command prompt
3. Pull a suitable model:
   ```bash
   ollama pull llama2
   # or for better performance:
   ollama pull mistral
   ```

### 4.2 Start Ollama Server
```bash
ollama serve
```

### 4.3 Test Ollama Connection
```bash
curl http://localhost:11434/api/generate -d '{
  "model": "llama2",
  "prompt": "Hello, how are you?",
  "stream": false
}'
```

## Part 5: Unity Scene Setup

### 5.1 Scene Hierarchy Setup
1. Create empty GameObject named "VRM_Controller"
2. Add your VRM avatar as child
3. Attach `VRMAnimationController` script to avatar
4. Attach `OllamaController` script to "VRM_Controller"

### 5.2 UI Setup
1. Create Canvas (UI → Canvas)
2. Add InputField for user input
3. Add Button for sending messages
4. Add Text component for chat display
5. Add ScrollRect for scrollable chat
6. Attach `ChatUI` script to Canvas

### 5.3 Link Components
1. Link all UI elements in ChatUI script
2. Link VRMAnimationController to OllamaController
3. Configure Ollama settings (URL, model name)
4. Set animation parameters in VRMAnimationController

## Part 6: Advanced Features

### 6.1 Voice Input Integration
Add Windows Speech Recognition:
```csharp
using UnityEngine.Windows.Speech;

public class VoiceInput : MonoBehaviour
{
    private DictationRecognizer dictationRecognizer;
    public OllamaController ollamaController;
    
    void Start()
    {
        dictationRecognizer = new DictationRecognizer();
        dictationRecognizer.DictationResult += OnDictationResult;
        dictationRecognizer.DictationError += OnDictationError;
    }
    
    public void StartListening()
    {
        dictationRecognizer.Start();
    }
    
    public void StopListening()
    {
        dictationRecognizer.Stop();
    }
    
    void OnDictationResult(string text, ConfidenceLevel confidence)
    {
        ollamaController.OnUserInput(text);
    }
    
    void OnDictationError(string error, int hresult)
    {
        Debug.LogError($"Voice input error: {error}");
    }
}
```

### 6.2 Multiple Avatar Support
Extend the system to control multiple VRM avatars:
```csharp
public class MultiAvatarController : MonoBehaviour
{
    public List<VRMAnimationController> avatars;
    public int activeAvatarIndex = 0;
    
    public void SwitchAvatar(int index)
    {
        if (index >= 0 && index < avatars.Count)
        {
            activeAvatarIndex = index;
        }
    }
    
    public void TriggerAnimationOnActiveAvatar(string keyword)
    {
        if (avatars[activeAvatarIndex] != null)
        {
            avatars[activeAvatarIndex].TriggerAnimation(keyword);
        }
    }
}
```

## Part 7: Testing and Troubleshooting

### 7.1 Common Issues
- **Ollama not responding**: Check if server is running on correct port
- **Animations not playing**: Verify Animator Controller setup and parameter names
- **Network errors**: Check firewall settings and localhost access
- **JSON parsing errors**: Ensure Newtonsoft.Json package is installed

### 7.2 Testing Checklist
- [ ] VRM model loads correctly
- [ ] Animations play manually
- [ ] Ollama server responds to curl requests
- [ ] Unity connects to Ollama successfully
- [ ] Animation keywords are extracted from responses
- [ ] UI updates correctly
- [ ] Auto-return to idle works

### 7.3 Performance Optimization
- Limit Ollama token count for faster responses
- Cache common animation combinations
- Use object pooling for multiple avatars
- Optimize animation transitions

## Part 8: Extending the System

### 8.1 Custom Animation Keywords
Add more specific animations and aliases to match your VRM model's capabilities.

### 8.2 Context Awareness
Implement conversation history to maintain context across interactions.

### 8.3 Emotion Persistence
Add mood states that influence animation selection over time.

### 8.4 Integration with Other Services
- TTS for voice output
- STT for voice input
- External APIs for enhanced responses

## Conclusion

This system creates a bridge between Ollama's LLM capabilities and Unity's VRM avatar system, allowing for dynamic, AI-controlled character animations based on natural language processing. The modular design allows for easy extension and customization based on your specific needs.

Remember to test thoroughly and adjust parameters based on your specific VRM models and desired interaction patterns.