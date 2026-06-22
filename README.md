# DeepBattler - Your BEST LLM Battlegrounds Coach/Friend！🍻🍻 <a id="english"></a>

**[English](#english)** | **[中文](#chinese)** | **[日本語](#japanese)**

### Well met, hero! I'm DeepBattler, the tavern master who brews brilliant plays, belly laughs, and more pep than a dancing Murloc on espresso! 🍻🐟

DeepBattler, a LLM-Driven Hearthstone Battlegrounds enthusiast like us. DeepBattler seamlessly integrates with the Hearthstone Deck Tracker (HDT) plugin to provide you with **real-time strategic advice**. Whether you're aiming to climb the ranks or just improve your game experience, DeepBattler has got your back!

DeepBattler's strength can match that of the **top 0.1% players on EU servers (8K ELO)**, thanks to its insightful, voice-assisted guidance that helps you make the best decisions on the fly. Let's take your gameplay to the next level!

**Demos can be found here! [YouTube Link](https://drive.google.com/file/d/1DY8hDdvVe-Iw7zKItOB1B-rvaf87l_Jc/view?usp=sharing)**

## ✨ New Features

### 🎯 Real-Time Visual Suggestion Window
- **In-Game Overlay**: A beautiful floating window displays DeepBattler's strategic suggestions directly in your game interface
- **Live Updates**: Suggestions update in real-time as the game state changes
- **Clear Formatting**: Easy-to-read bullet points with larger, clearer fonts
- **Position Control**: Draggable window that stays in your preferred location (default: bottom-left corner)

### 🎤 Voice + Text Dual Output
- **Voice Interaction**: Natural voice conversation using Google Gemini Live API
- **Text Display**: Simultaneous text output using Gemini 2.5 Flash Lite for visual reference
- **Parallel Processing**: Audio and text responses generated simultaneously for the best of both worlds
- **Smart Updates**: Text suggestions automatically refresh with each agent response

### 🔄 Dynamic Game State Integration
- **Auto-Detection**: Automatically detects when a game starts and adapts accordingly
- **Real-Time Monitoring**: Continuously monitors game state changes and updates system prompts
- **Casual Chat Mode**: When no game is active, DeepBattler switches to friendly conversation mode
- **Seamless Transitions**: Smoothly transitions between game mode and chat mode

## System Components  

### 1. Hearthstone Deck Tracker (HDT) Plugin - Real-Time Data Collection API  
The DeepBattler Plugin serves as a **real-time API endpoint for Battleground Board data**, continuously monitoring and capturing all board state information during gameplay.

- **Real-Time Monitoring:** Continuously tracks your game state as it happens, capturing every change in real-time
- **Comprehensive Data Collection:** Records all board data including:
  - Player hero information (name, health, hero power with cost)
  - Resources (available gold, tavern tier, upgrade costs)
  - Board state (warband minions, hand cards, tavern offerings)
  - Game phase and turn information
  - Battle results and health changes
- **JSON Outputs:** Provides clear, structured JSON data for easy consumption
- **Local Storage:** Automatically saves game state snapshots to local files for analysis
- **Efficient Data Handling:** Ensures smooth performance with minimal impact on game performance
- **API Endpoint Functionality:** Acts as a live data feed that other components can consume  

### 2. RAG-Powered LLM Agent  
The DeepBattler Agent is a **Retrieval-Augmented Generation (RAG) system** that combines real-time game state data with strategic knowledge to provide intelligent guidance.

- **RAG Architecture:** Retrieves relevant game state information and augments it with strategic knowledge for context-aware responses
- **Advanced Analysis:** Utilizes powerful language model capabilities (Google Gemini Live + Gemini 2.5 Flash Lite)
- **Real-Time Data Integration:** Consumes live game state data from the plugin API endpoint
- **Strategic Advice:** Provides real-time tactical recommendations based on current board state
- **Voice Communication:** Interact naturally with voice commands via microphone
- **Text Display:** Visual text suggestions displayed in an overlay window
- **Adaptive Decisions:** Adjusts strategies based on different game scenarios and board states
- **Dual API Architecture:** Parallel audio (Live API) and text (generate_content API) generation
- **Context-Aware Responses:** Uses retrieved game state data to provide relevant, timely advice

### 3. GRPO-Trained RL Policy (Advanced) 🚀
DeepBattler also includes a **Group Relative Policy Optimization (GRPO)** trained reinforcement learning policy for advanced strategic decision-making.

- **GRPO Training:** State-of-the-art RL algorithm trained on extensive Battlegrounds gameplay data
- **Optimal Decision Making:** Learns from expert-level gameplay to provide superior strategic recommendations
- **Model Availability:** The GRPO-trained model is available on HuggingFace for research and advanced use cases
- **Performance:** Achieves performance comparable to top-tier players through learned policy optimization
- **HuggingFace Integration:** Easy access to pre-trained models and checkpoints

**🔗 Access the GRPO model on HuggingFace:** [https://huggingface.co/spaces/iteratehack/deepbattler/tree/main](https://huggingface.co/spaces/iteratehack/deepbattler/tree/main)  

## Setup and Configuration  

### Plugin Setup  
1. **Open the `DeepBattlerPlugin/DeepBattlerPlugin.csproj` file.**  
   - Instead of modifying individual class files, ensure your project references are correctly set up in the `.csproj` file.

2. **Add Dependencies:**  
   To ensure **DeepBattlerPlugin** functions correctly, you only need to add the following two dependencies:
   
   1. **HearthDb.dll**
   2. **HearthstoneDeckTracker.exe**

   #### Adding Dependencies to Your Visual Studio Project
   
   Follow these steps to add the two dependencies to your Visual Studio project:
   
   1. **Open Your Project**
      - Open your plugin project in Visual Studio (e.g., `DeepBattlerPlugin`).
   
   2. **Add References**
      - Right-click on the project name and select **"Add"** > **"Reference..."**.
   
   3. **Browse and Select Dependencies**
      - In the **"Reference Manager"** window, select the **"Browse"** tab.
      - Click the **"Browse"** button and navigate to the directory containing `HearthDb.dll` and `HearthstoneDeckTracker.exe`.
        - **HearthDb.dll**: Typically located in the HDT installation directory.
        - **HearthstoneDeckTracker.exe**: Also located in the HDT installation directory.
      - Select both files and click **"Add"**.
   
   4. **Confirm Addition**
      - After adding, click **"OK"** to confirm the references.
   
   #### Setting "Copy Local" Property (Optional)
   
   To ensure these dependencies are copied to the output directory during the build process, set their **"Copy Local"** property to **"True"**:
   
   1. **Expand References**
      - In the **"Solution Explorer"**, expand the **"References"** node.
   
   2. **Set Properties**
      - Select the recently added `HearthDb.dll` and `HearthstoneDeckTracker.exe` references.
      - Right-click each reference and choose **"Properties"**.
      - In the **Properties** window, set **"Copy Local"** to **"True"**.
   
   #### Important Notes
   
   - **Compatibility**: Ensure that the versions of `HearthDb.dll` and `HearthstoneDeckTracker.exe` you are using are compatible with your current version of **Hearthstone Deck Tracker (HDT)** to avoid potential compatibility issues.
   - **Plugin Directory**: After completing the above steps, make sure to place the compiled `DeepBattlerPlugin.dll` into HDT's `Plugins` folder so that HDT can correctly load your plugin.

3. **Configure the Plugin Path**  
   - Open the `DeepBattlerPlugin/DeepBattlerPlugin.csproj` file.
   - Set the `_path` variable to your absolute game state file path:
     ```csharp  
     private readonly string _path = @"C:\Your\Absolute\Path\To\game_state.json";  
     ```  

4. **Build the Plugin**  
   - Build the plugin. The compiled `DeepBattlerPlugin.dll` will be located under `DeepBattlerPlugin/bin/Debug`.

5. **Install the Plugin in HDT**  
   1. Open Hearthstone Deck Tracker (HDT).
   2. Copy the plugin files to the HDT plugins directory:
      - Default location: `%AppData%\Hearthstone Deck Tracker\Plugins`
   3. Launch Hearthstone Deck Tracker.
   4. Enable the plugin in HDT under `Options -> Plugins`.
   
   ![HDT Plugin Setup](https://github.com/user-attachments/assets/23f41637-d517-4b79-87d5-cc6e5009ac24)

### LLM Agent Setup  

#### Using Google Gemini Live (Recommended) 🎤
1. **Install the required Python packages:**  
   ```bash  
   pip install google-genai python-dotenv pyaudio
   ```  
   
2. **Set up your API key:**
   - Create a `.env` file in the `Agent/real_time_caller/` directory
   - Add your Google Gemini API key:
     ```
     GEMINI_API_KEY=your-api-key-here
     ```
   - Get your API key from: https://ai.google.dev/
   
3. **Launch the LLM agent:**  
   ```bash  
   cd Agent/real_time_caller
   python gemini_live.py
   ```  
   
4. **Features:**
   - **Voice Interaction**: Speak naturally to DeepBattler via microphone
   - **Real-Time Suggestions**: Visual text window shows strategic advice
   - **Auto Game Detection**: Automatically adapts when a game starts
   - **Dynamic Updates**: System prompts update as game state changes

---

#### Using Claude Code — Claude Max subscription (No API key) 🦞

If you have a **Claude Max** (or Pro) subscription, you can drive DeepBattler through the local **Claude Code CLI** instead of a paid API key. Each suggestion runs `claude -p` headlessly under your subscription login — no `ANTHROPIC_API_KEY` and no per-token billing.

1. **Install Claude Code and log in once:**
   - Install (see https://docs.claude.com/en/docs/claude-code), e.g. `npm install -g @anthropic-ai/claude-code`
   - Run `claude` once, then `/login` and choose your Claude account (subscription).

2. **(Optional) Voice output:**
   ```bash
   pip install pyttsx3      # only needed if you want spoken advice (offline)
   ```

3. **Run the caller:**
   ```bash
   cd Agent/real_time_caller
   python claude_caller.py                 # default model: sonnet, persistent session ON
   python claude_caller.py --model opus    # higher-quality advice
   python claude_caller.py --tts           # also speak the advice aloud
   python claude_caller.py --no-session    # independent calls (re-send the guide each turn)
   ```

4. **How it works:**
   - Watches `latest_game_state.json` (written by the HDT plugin) and, on each change, asks Claude for one concise recommendation for the current turn.
   - Writes the advice to `agent_output.txt`, which the in-game overlay window displays in real time.
   - **Keeps one Claude conversation alive per game** (via `--session-id`/`--resume`): the strategy guide (`Prompt.txt`) is sent only on the first turn, and later turns send just the new game state, so Claude remembers prior turns and you never re-explain the rules. A fresh conversation starts automatically when a new game begins. Use `--no-session` to disable.
   - Strips `ANTHROPIC_API_KEY` from the call so it always uses your subscription, not API billing.
   - `python claude_caller.py --once` evaluates the current state a single time (handy for a quick test without a live game).

> **Notes:** Requests count toward your Claude subscription usage limits (not per-token API billing). Latency is slightly higher than a raw API call due to CLI startup, which is fine for turn-based play. Claude has no native voice API, so `--tts` uses a local text-to-speech engine. Paths default to `%Desktop%\DeepBattler\Agent`; if your repo lives elsewhere, set the `DEEPBATTLER_AGENT_DIR` environment variable (the plugin, overlay, and this script all honor it).

---

#### Using OpenAI GPT (Legacy)  
1. **Install the required Python packages:**  
   ```bash  
   pip install openai playsound==1.2.2  
   ```  
   *Note: Version 1.2.2 of `playsound` is required for compatibility.*  
   
2. **Add your OpenAI API key in `Openai_caller.py`:**  
   ```python  
   api_key = "your-openai-api-key-here"  
   ```  
   
3. **Launch the LLM agent:**  
   ```bash  
   python Openai_caller.py
   ```  

---

#### Using Google Gemma (Legacy)  
1. **Install the required Python packages:**  
   ```bash  
   pip install keras_hub jax keras gtts playsound==1.2.2
   ```  
   *Note: Version 1.2.2 of `playsound` is required for compatibility.*  
   
2. **Set up the Gemma environment:**  
   Your script (`Gemma_caller.py`) includes the following environment configurations:
   ```python
   import os
   os.environ["KERAS_BACKEND"] = "jax"
   os.environ["XLA_PYTHON_CLIENT_MEM_FRACTION"] = "1.00"
   ```

3. **Prepare the necessary files:**
   - `game_state.json`: A JSON file to provide the current game state.
   - `Prompt.txt`: A text file containing the system prompt for Gemma.

4. **Run the Gemma agent:**
   ```bash
   python Gemma_caller.py
   ```

## Custom Non-Commercial License  

© [2024] [William-Dic]  

You’re free to use, copy, modify, and share this software for personal, educational, or non-commercial purposes. Here’s what you need to know:

1. **Non-Commercial Use**  
   Feel free to use and tweak the software, but don’t sell or distribute it commercially without permission.

2. **Hearthstone Intellectual Property**  
   This tool uses assets from Blizzard Entertainment’s Hearthstone. Make sure to follow Blizzard’s terms when using DeepBattler. This tool isn’t affiliated with or endorsed by Blizzard.

3. **Acknowledgment of External Contributions**  
   DeepBattler includes components from Hearthstone Deck Tracker (HDT) by HearthSim. All rights to HDT belong to HearthSim and its contributors. This doesn’t imply any ownership or endorsement by HearthSim.

4. **No Warranty**  
   The software is provided "as is." We aren’t responsible for any issues that arise from using it.

5. **Derivative Works**  
   If you modify or build upon this software, include this license and follow its terms.

6. **Redistribution**  
   If you share the software or any derivatives, keep this license and the copyright notices.

By using DeepBattler, you agree to these terms.

[William-Dic]  
[2024]

---

# DeepBattler - 你的专属大模型酒馆战棋助手！ 🍻🍻 <a id="chinese"></a>

**[English](#english)** | **[中文](#chinese)** | **[日本語](#japanese)**

### 英雄，好久不见！我是DeepBattler——一位既能端出妙计良策，又能端出热茶闲聊的酒馆掌柜，嘴皮子比鱼人还溜，招式比醉拳还灵！🍵🐟 

DeepBattler，是一款专为《炉石传说》酒馆战棋打造的先进助手。由大语言模型（LLM）驱动，集成了海量的游戏数据和随从选择分析，作者也提供了开放的串口，让你可以非常轻易地修改并添加你的偏好。DeepBattler无缝集成《炉石传说》卡组跟踪器（HDT）插件，为你提供**实时战略建议**。无论你是想提升排名还是改善游戏技巧，DeepBattler都能助你一臂之力！

DeepBattler的实力可以匹敌**欧服排名前0.1%的玩家**，得益于其深入的语音辅助指导，帮助你在关键时刻做出最佳决策。让我们一起提升你的游戏水平吧！

## ✨ 新功能特性

### 🎯 实时可视化建议窗口
- **游戏内覆盖层**：精美的浮动窗口直接在游戏界面中显示DeepBattler的战略建议
- **实时更新**：随着游戏状态变化，建议实时更新
- **清晰格式**：易于阅读的项目符号，字体更大更清晰
- **位置控制**：可拖拽窗口，保持在您喜欢的位置（默认：左下角）

### 🎤 语音+文字双输出
- **语音交互**：使用Google Gemini Live API进行自然语音对话
- **文字显示**：同时使用Gemini 2.5 Flash Lite生成文字输出，方便视觉参考
- **并行处理**：音频和文字响应同时生成，两全其美
- **智能更新**：每次agent响应时，文字建议自动刷新

### 🔄 动态游戏状态集成
- **自动检测**：自动检测游戏开始并相应调整
- **实时监控**：持续监控游戏状态变化并更新系统提示
- **休闲聊天模式**：当没有游戏活动时，DeepBattler切换到友好对话模式
- **无缝切换**：在游戏模式和聊天模式之间平滑切换

## 系统组件  

### 1. 《炉石传说》卡组跟踪器（HDT）插件 - 实时数据采集API  
DeepBattler 插件作为**战棋棋盘数据的实时API端点**，持续监控并捕获游戏过程中的所有棋盘状态信息。

- **实时监控:** 持续跟踪你的游戏状态，实时捕获每一个变化
- **全面数据采集:** 记录所有棋盘数据，包括：
  - 玩家英雄信息（名称、生命值、英雄技能及费用）
  - 资源信息（可用金币、酒馆等级、升级费用）
  - 棋盘状态（战场随从、手牌、酒馆选项）
  - 游戏阶段和回合信息
  - 战斗结果和生命值变化
- **JSON输出:** 提供清晰、结构化的JSON数据，便于使用
- **本地存储:** 自动将游戏状态快照保存到本地文件以供分析
- **高效数据处理:** 确保流畅运行，对游戏性能影响最小
- **API端点功能:** 作为实时数据流，供其他组件使用  

### 2. RAG驱动的LLM代理  
DeepBattler 代理是一个**检索增强生成（RAG）系统**，结合实时游戏状态数据和战略知识，提供智能指导。

- **RAG架构:** 检索相关游戏状态信息，并用战略知识增强，实现上下文感知响应
- **高级分析:** 利用强大的语言模型功能（Google Gemini Live + Gemini 2.5 Flash Lite）
- **实时数据集成:** 从插件API端点消费实时游戏状态数据
- **战略建议:** 基于当前棋盘状态提供实时战术建议
- **语音通信:** 通过麦克风进行自然语音交互
- **文字显示:** 在覆盖窗口中显示可视化文字建议
- **自适应决策:** 根据不同游戏情境和棋盘状态调整策略
- **双API架构:** 并行生成音频（Live API）和文字（generate_content API）
- **上下文感知响应:** 使用检索到的游戏状态数据提供相关、及时的建议

### 3. GRPO训练的强化学习策略（高级版）🚀
DeepBattler 还包含一个**组相对策略优化（GRPO）**训练的强化学习策略，用于高级战略决策。

- **GRPO训练:** 基于大量战棋游戏数据训练的最先进强化学习算法
- **最优决策:** 从专家级游戏玩法中学习，提供卓越的战略建议
- **模型可用性:** GRPO训练的模型已在 HuggingFace 上提供，供研究和高级用例使用
- **性能表现:** 通过学习的策略优化，达到与顶级玩家相当的性能
- **HuggingFace集成:** 轻松访问预训练模型和检查点

**🔗 在 HuggingFace 上访问 GRPO 模型：** [https://huggingface.co/spaces/iteratehack/deepbattler/tree/main](https://huggingface.co/spaces/iteratehack/deepbattler/tree/main)  

## 设置与配置  

### 插件设置  
1. **打开 `DeepBattlerPlugin/DeepBattlerPlugin.csproj` 文件。**  
   - 不再修改单个类文件，而是确保项目引用在 `.csproj` 文件中正确设置。

2. **添加依赖项:**  
   为了确保 **DeepBattlerPlugin** 正常运行，您仅需添加以下两个依赖项：
   
   1. **HearthDb.dll**
   2. **HearthstoneDeckTracker.exe**

   #### 将依赖项添加到 Visual Studio 项目
   
   请按照以下步骤在 Visual Studio 中添加这两个依赖项：
   
   1. **打开您的项目**
      - 在 Visual Studio 中打开您的插件项目（例如，DeepBattlerPlugin）。
   
   2. **添加引用**
      - 右键点击项目名称，选择 **“添加”** > **“引用...”**。
   
   3. **浏览并选择依赖项**
      - 在弹出的 **“引用管理器”** 窗口中，选择 **“浏览”** 选项卡。
      - 点击 **“浏览”** 按钮，导航到包含 `HearthDb.dll` 和 `HearthstoneDeckTracker.exe` 的目录。
        - **HearthDb.dll**：通常位于 HDT 的安装目录下。
        - **HearthstoneDeckTracker.exe**：同样位于 HDT 的安装目录中。
      - 选择这两个文件后，点击 **“添加”**。
   
   4. **确认添加**
      - 添加完毕后，点击 **“确定”** 以确认引用。
   
   #### 设置“复制到本地”属性（可选）
   
   为了确保在构建项目时，这些依赖项会被复制到输出目录，您可以设置它们的 **“复制到本地”** 属性：
   
   1. **展开引用**
      - 在 **“解决方案资源管理器”** 中，展开 **“引用”**（**References**）。
   
   2. **设置属性**
      - 选择刚刚添加的 `HearthDb.dll` 和 `HearthstoneDeckTracker.exe` 引用。
      - 右键点击每个引用，选择 **“属性”**。
      - 在属性窗口中，将 **“复制到本地”**（**Copy Local**） 设置为 **“True”**。
   
   #### 注意事项
   
   - **兼容性**：确保您使用的 `HearthDb.dll` 和 `HearthstoneDeckTracker.exe` 版本与您当前的 **Hearthstone Deck Tracker (HDT)** 版本兼容，以避免潜在的兼容性问题。
   - **插件目录**：完成上述步骤后，确保将编译生成的 `DeepBattlerPlugin.dll` 放置在 HDT 的 `Plugins` 文件夹中，以便 HDT 能够正确加载您的插件。

3. **配置插件路径**  
   - 打开 `DeepBattlerPlugin/DeepBattlerPlugin.csproj` 文件。
   - 将 `_path` 变量设置为你的 `game_state.json` 的绝对路径：
     ```csharp  
     private readonly string _path = @"C:\Your\Absolute\Path\To\game_state.json";  
     ```  

4. **构建插件**  
   - 构建插件。编译后的 `DeepBattlerPlugin.dll` 位于 `DeepBattlerPlugin/bin/Debug` 目录下。

5. **安装插件到HDT**  
   1. 打开《炉石传说》卡组跟踪器（HDT）。
   2. 将插件文件复制到HDT的插件目录：
      - 默认位置：`%AppData%\Hearthstone Deck Tracker\Plugins`
   3. 启动《炉石传说》卡组跟踪器。
   4. 在HDT的 `选项 -> 插件` 下启用插件。
   
   ![HDT插件设置](https://github.com/user-attachments/assets/23f41637-d517-4b79-87d5-cc6e5009ac24)

### LLM代理设置  

#### 使用Google Gemini Live（推荐）🎤
1. **安装所需的Python包：**  
   ```bash  
   pip install google-genai python-dotenv pyaudio
   ```  
   
2. **设置API密钥：**
   - 在 `Agent/real_time_caller/` 目录下创建 `.env` 文件
   - 添加您的Google Gemini API密钥：
     ```
     GEMINI_API_KEY=your-api-key-here
     ```
   - 从以下地址获取API密钥：https://ai.google.dev/
   
3. **启动LLM代理：**  
   ```bash  
   cd Agent/real_time_caller
   python gemini_live.py
   ```  
   
4. **功能特性：**
   - **语音交互**：通过麦克风自然与DeepBattler对话
   - **实时建议**：可视化文字窗口显示战略建议
   - **自动游戏检测**：游戏开始时自动适配
   - **动态更新**：系统提示随游戏状态变化而更新

---

#### 使用 Claude Code —— Claude Max 订阅（无需 API key）🦞

如果你有 **Claude Max**（或 Pro）订阅，可以透过本地的 **Claude Code CLI** 来驱动 DeepBattler，而不需要付费 API key。每次建议都以 `claude -p` 无界面模式、用你的订阅登入身份执行 —— 不需要 `ANTHROPIC_API_KEY`，也没有按 token 计费。

1. **安装 Claude Code 并登入一次：**
   - 安装（见 https://docs.claude.com/en/docs/claude-code），例如 `npm install -g @anthropic-ai/claude-code`
   - 执行一次 `claude`，然后 `/login` 选择你的 Claude 账号（订阅）。

2. **（可选）语音输出：**
   ```bash
   pip install pyttsx3      # 只有需要语音朗读时才安装（离线）
   ```

3. **运行：**
   ```bash
   cd Agent/real_time_caller
   python claude_caller.py                 # 默认模型：sonnet，持续会话开启
   python claude_caller.py --model opus    # 更高质量的建议
   python claude_caller.py --tts           # 同时朗读建议
   python claude_caller.py --no-session    # 每次独立调用（每回合重发策略指南）
   ```

4. **运行原理：**
   - 监看 HDT 插件写入的 `latest_game_state.json`，每次变化就向 Claude 请求一句当前回合的简洁建议。
   - 将建议写入 `agent_output.txt`，游戏内浮动窗口会实时显示。
   - **每局保持同一个 Claude 对话**（透过 `--session-id`/`--resume`）：策略指南（`Prompt.txt`）只在第一回合送出，之后每回合只送新的游戏状态，Claude 会记得先前回合，你不必重讲规则。新对局开始时会自动开启新对话。用 `--no-session` 可关闭。
   - 调用时会移除 `ANTHROPIC_API_KEY`，确保始终走订阅而非 API 计费。
   - `python claude_caller.py --once` 只评估当前状态一次（方便快速测试）。

> **说明：** 请求会计入你的 Claude 订阅用量额度（而非按 token 的 API 计费）。由于 CLI 启动，延迟会比裸 API 调用略高，对回合制游戏来说完全够用。Claude 没有原生语音 API，所以 `--tts` 使用本地的文字转语音引擎。路径默认为 `%Desktop%\DeepBattler\Agent`；若你的 repo 在其他位置，设置环境变量 `DEEPBATTLER_AGENT_DIR`（插件、浮动窗口与本脚本都会读取它）。

---

#### 使用OpenAI GPT（旧版）  
1. **安装所需的Python包：**  
   ```bash  
   pip install openai playsound==1.2.2  
   ```  
   *注意：需要兼容性，请使用 `playsound` 的1.2.2版本。*  
   
2. **在 `Openai_caller.py` 中添加你的OpenAI API密钥：**  
   ```python  
   api_key = "your-openai-api-key-here"  
   ```  
   
3. **启动LLM代理：**  
   ```bash  
   python Openai_caller.py  
   ```  

## 自定义非商业许可证

© [2024] [William-Dic]

您可以自由地为个人、教育或非商业目的使用、复制、修改和分享本软件。以下是您需要了解的内容：

1. **非商业使用**  
   您可以自由使用和调整本软件，但未经许可不得将其用于商业销售或分发。

2. **《炉石传说》知识产权**  
   本工具使用了暴雪娱乐的《炉石传说》中的资产。使用DeepBattler时，请确保遵守暴雪的条款。本工具与暴雪无关联，也未得到暴雪的认可。

3. **承认外部贡献**  
   DeepBattler包含了HearthSim开发的《炉石传说》卡组跟踪器（HDT）的组件。HDT及其组件的所有权归HearthSim及其贡献者所有。这不意味着HearthSim拥有或认可本工具。

4. **无担保**  
   本软件按“原样”提供。我们对因使用本软件而产生的任何问题不承担责任。

5. **衍生作品**  
   如果您修改或基于本软件开发衍生作品，请包含本许可证并遵守其条款。

6. **再分发**  
   如果您分享本软件或任何衍生作品，请保留本许可证和版权声明。

使用DeepBattler，即表示您同意这些条款。

[William-Dic]  
[2024]

---

# DeepBattler - あなた専用の大型モデル Battlegrounds アシスタント！ 🍻🍻 <a id="japanese"></a>

**[English](#english)** | **[中文](#chinese)** | **[日本語](#japanese)**

### お久しぶりです、英雄！私はDeepBattler、妙案も熱いお茶も提供する酒場のマスターです！口の回転はムルロックより速く、動きは居合斬りよりキレがある…でも足はちゃっかり畳に引っかかるタイプです！

DeepBattlerへようこそ。『ハースストーン』のバトルグラウンド向けに特化した最新のアシスタントです。大型言語モデル（LLM）を搭載し、『ハースストーン』デックトラッカー（HDT）プラグインとシームレスに統合して、**リアルタイムの戦略アドバイス**を提供します。ランキングを上げたい方も、ゲームスキルを向上させたい方も、DeepBattlerがサポートします！

DeepBattlerの実力は**EUサーバーの上位0.1%のプレイヤーに匹敵します**。音声支援ガイダンスにより、重要な場面で最適な判断を下す手助けをします。さあ、一緒にゲームをレベルアップしましょう！

## ✨ 新機能

### 🎯 リアルタイム視覚的提案ウィンドウ
- **ゲーム内オーバーレイ**：美しいフローティングウィンドウがゲームインターフェースに直接DeepBattlerの戦略的提案を表示
- **ライブ更新**：ゲーム状態が変化すると、提案がリアルタイムで更新されます
- **明確なフォーマット**：より大きく、より明確なフォントで読みやすい箇条書き
- **位置制御**：好みの位置に固定できるドラッグ可能なウィンドウ（デフォルト：左下角）

### 🎤 音声+テキストデュアル出力
- **音声インタラクション**：Google Gemini Live APIを使用した自然な音声会話
- **テキスト表示**：視覚的参照のためにGemini 2.5 Flash Liteを使用した同時テキスト出力
- **並列処理**：音声とテキストの応答が同時に生成され、両方の利点を享受
- **スマート更新**：エージェントの応答ごとにテキスト提案が自動的に更新されます

### 🔄 動的ゲーム状態統合
- **自動検出**：ゲームが開始されると自動的に検出し、それに応じて適応
- **リアルタイム監視**：ゲーム状態の変化を継続的に監視し、システムプロンプトを更新
- **カジュアルチャットモード**：ゲームがアクティブでない場合、DeepBattlerはフレンドリーな会話モードに切り替わります
- **シームレスな切り替え**：ゲームモードとチャットモードの間をスムーズに切り替え

## システムコンポーネント  

### 1. 『ハースストーン』デックトラッカー（HDT）プラグイン - リアルタイムデータ収集API  
DeepBattlerプラグインは、**バトルグラウンドボードデータのリアルタイムAPIエンドポイント**として機能し、ゲームプレイ中にすべてのボード状態情報を継続的に監視およびキャプチャします。

- **リアルタイム監視:** ゲーム状態をリアルタイムで継続的に追跡し、すべての変化をリアルタイムでキャプチャ
- **包括的なデータ収集:** すべてのボードデータを記録：
  - プレイヤーヒーロー情報（名前、体力、ヒーローパワーとコスト）
  - リソース情報（利用可能なゴールド、酒場ティア、アップグレードコスト）
  - ボード状態（戦場のミニオン、手札、酒場のオプション）
  - ゲームフェーズとターン情報
  - バトル結果と体力変化
- **JSON出力:** 明確で構造化されたJSONデータを提供し、簡単に使用可能
- **ローカルストレージ:** 分析のためにゲーム状態スナップショットをローカルファイルに自動保存
- **効率的なデータ処理:** ゲームパフォーマンスへの影響を最小限に抑えながら、スムーズなパフォーマンスを保証
- **APIエンドポイント機能:** 他のコンポーネントが消費できるライブデータフィードとして機能  

### 2. RAG搭載LLMエージェント  
DeepBattlerエージェントは、リアルタイムのゲーム状態データと戦略的知識を組み合わせて、インテリジェントなガイダンスを提供する**検索拡張生成（RAG）システム**です。

- **RAGアーキテクチャ:** 関連するゲーム状態情報を検索し、戦略的知識で拡張して、コンテキスト認識応答を実現
- **高度な分析:** 強力な言語モデル機能を活用（Google Gemini Live + Gemini 2.5 Flash Lite）
- **リアルタイムデータ統合:** プラグインAPIエンドポイントからリアルタイムのゲーム状態データを消費
- **戦略的アドバイス:** 現在のボード状態に基づいてリアルタイムで戦術的な提案を提供
- **音声コミュニケーション:** マイクを通じた自然な音声インタラクション
- **テキスト表示:** オーバーレイウィンドウに視覚的なテキスト提案を表示
- **適応型の意思決定:** ゲームの状況とボード状態に応じて戦略を調整
- **デュアルAPIアーキテクチャ:** 音声（Live API）とテキスト（generate_content API）の並列生成
- **コンテキスト認識応答:** 検索されたゲーム状態データを使用して、関連性があり、タイムリーなアドバイスを提供

### 3. GRPO訓練された強化学習ポリシー（上級版）🚀
DeepBattlerには、高度な戦略的意思決定のための**グループ相対ポリシー最適化（GRPO）**訓練された強化学習ポリシーも含まれています。

- **GRPO訓練:** 広範なバトルグラウンドゲームプレイデータで訓練された最先端のRLアルゴリズム
- **最適な意思決定:** エキスパートレベルのゲームプレイから学習し、優れた戦略的提案を提供
- **モデル可用性:** GRPO訓練されたモデルは、研究および高度なユースケースのためにHuggingFaceで利用可能
- **パフォーマンス:** 学習されたポリシー最適化を通じて、トップティアプレイヤーに匹敵するパフォーマンスを達成
- **HuggingFace統合:** 事前訓練されたモデルとチェックポイントへの簡単なアクセス

**🔗 HuggingFaceでGRPOモデルにアクセス：** [https://huggingface.co/spaces/iteratehack/deepbattler/tree/main](https://huggingface.co/spaces/iteratehack/deepbattler/tree/main)  

## セットアップと構成  

### プラグインセットアップ  
1. **`DeepBattlerPlugin/DeepBattlerPlugin.csproj` ファイルを開きます。**  
   - 個々のクラスファイルを変更する代わりに、`.csproj` ファイル内でプロジェクトの参照が正しく設定されていることを確認してください。

2. **依存関係を追加する:**  
   **DeepBattlerPlugin** が正しく機能するために、以下の2つの依存関係を追加する必要があります：
   
   1. **HearthDb.dll**
   2. **HearthstoneDeckTracker.exe**

   #### Visual Studio プロジェクトに依存関係を追加する方法
   
   以下の手順に従って、Visual Studio プロジェクトにこれらの依存関係を追加してください：
   
   1. **プロジェクトを開く**
      - Visual Studio でプラグインプロジェクト（例：DeepBattlerPlugin）を開きます。
   
   2. **参照を追加する**
      - プロジェクト名を右クリックし、**「追加」** > **「参照...」** を選択します。
   
   3. **依存関係をブラウズして選択する**
      - ポップアップした **「参照マネージャー」** ウィンドウで、**「ブラウズ」** タブを選択します。
      - **「ブラウズ」** ボタンをクリックし、`HearthDb.dll` と `HearthstoneDeckTracker.exe` が含まれるディレクトリに移動します。
        - **HearthDb.dll**：通常、HDTのインストールディレクトリにあります。
        - **HearthstoneDeckTracker.exe**：同様に、HDTのインストールディレクトリにあります。
      - 両方のファイルを選択し、**「追加」** をクリックします。
   
   4. **追加を確認する**
      - 追加が完了したら、**「OK」** をクリックして参照を確認します。
   
   #### 「コピー ローカル」プロパティの設定（オプション）
   
   ビルドプロセス中にこれらの依存関係が出力ディレクトリにコピーされるようにするために、**「コピー ローカル」** プロパティを **「True」** に設定します：
   
   1. **参照を展開する**
      - **「ソリューションエクスプローラー」** で、**「参照」**（**References**）ノードを展開します。
   
   2. **プロパティを設定する**
      - 追加した `HearthDb.dll` と `HearthstoneDeckTracker.exe` の参照を選択します。
      - 各参照を右クリックし、**「プロパティ」** を選択します。
      - **プロパティウィンドウ**で、**「コピー ローカル」**（**Copy Local**） を **「True」** に設定します。
   
   #### 注意事項
   
   - **互換性**：使用している `HearthDb.dll` と `HearthstoneDeckTracker.exe` のバージョンが現在の **Hearthstone Deck Tracker (HDT)** のバージョンと互換性があることを確認してください。互換性の問題を避けるためです。
   - **プラグインディレクトリ**：上記の手順を完了した後、コンパイルされた `DeepBattlerPlugin.dll` を HDT の `Plugins` フォルダに配置し、HDT がプラグインを正しくロードできるようにしてください。

3. **プラグインパスの設定**  
   - `DeepBattlerPlugin/DeepBattlerPlugin.csproj` ファイルを開きます。
   - `_path` 変数をあなたの `game_state.json` の絶対パスに設定します：
     ```csharp  
     private readonly string _path = @"C:\Your\Absolute\Path\To\game_state.json";  
     ```  

4. **プラグインをビルドする**  
   - プラグインをビルドします。コンパイルされた `DeepBattlerPlugin.dll` は `DeepBattlerPlugin/bin/Debug` に配置されます。

5. **HDTへのプラグインのインストール**  
   1. 『ハースストーン』デックトラッカー（HDT）を開きます。
   2. プラグインファイルをHDTのプラグインディレクトリにコピーします：
      - デフォルトの場所：`%AppData%\Hearthstone Deck Tracker\Plugins`
   3. 『ハースストーン』デックトラッカーを起動します。
   4. HDTの `オプション -> プラグイン` でプラグインを有効にします。
   
   ![HDTプラグイン設定](https://github.com/user-attachments/assets/23f41637-d517-4b79-87d5-cc6e5009ac24)

### LLMエージェントのセットアップ

#### Google Gemini Liveを使用する場合（推奨）🎤

1. **必要なPythonパッケージをインストールします:**
```bash
pip install google-genai python-dotenv pyaudio
```

2. **APIキーを設定します:**
   - `Agent/real_time_caller/` ディレクトリに `.env` ファイルを作成
   - Google Gemini APIキーを追加：
     ```
     GEMINI_API_KEY=your-api-key-here
     ```
   - 以下のURLからAPIキーを取得：https://ai.google.dev/

3. **LLMエージェントを起動します:**
```bash
cd Agent/real_time_caller
python gemini_live.py
```

4. **機能:**
   - **音声インタラクション**：マイクを通じてDeepBattlerと自然に会話
   - **リアルタイム提案**：視覚的なテキストウィンドウが戦略的アドバイスを表示
   - **自動ゲーム検出**：ゲームが開始されると自動的に適応
   - **動的更新**：ゲーム状態の変化に応じてシステムプロンプトが更新されます

---

#### OpenAI GPTを使用する場合（旧版）

1. **必要なPythonパッケージをインストールします:**
```bash
pip install openai playsound==1.2.2
```
*注意：互換性のため、`playsound`のバージョンは必ず`1.2.2`を使用してください。*

2. **OpenAIのAPIキーを`Openai_caller.py`に設定します:**
```python
api_key = "your-openai-api-key-here"
```

3. **LLMエージェントを起動します:**
```bash
python Openai_caller.py
```

---

#### Google Gemmaのセットアップ方法（旧版）

Gemmaを使ったLLMエージェントの設定および起動方法は以下の通りです。

1. **必要なPythonパッケージをインストールします:**
```bash
pip install keras_hub jax keras gtts playsound==1.2.2
```
*注意：playsoundは互換性のため必ずバージョン1.2.2を使用してください。*

2. **Gemma用の環境を設定します:**  
スクリプト（`Gemma_caller.py`）に以下の環境設定を含めてください:
```python
import os

os.environ["XLA_PYTHON_CLIENT_MEM_FRACTION"] = "1.00"
os.environ["KERAS_BACKEND"] = "jax"
```

3. **Gemma用の必要ファイルを準備します:**  
以下のファイルが必要です:

- `game_state.json`：リアルタイムのゲーム状態データ（JSON形式）
- `Prompt.txt`：Gemmaのシステムプロンプトを記載したテキストファイル

4. **Gemmaエージェントを起動します:**
```bash
python Gemma_caller.py
```

## カスタム非商用ライセンス

© [2024] [William-Dic]

本ソフトウェアを個人、教育、非商用目的で使用、コピー、修正、共有することが自由に許可されています。以下の内容を確認してください：

1. **非商用利用**  
   本ソフトウェアを自由に使用および調整できますが、許可なく商業目的で販売または配布しないでください。

2. **ハースストーンの知的財産**  
   本ツールは、ブリザード・エンターテイメントのハースストーンのアセットを使用しています。DeepBattlerを使用する際は、ブリザードの利用規約を遵守してください。本ツールはブリザードと提携しておらず、ブリザードからの承認も受けていません。

3. **外部貢献の認識**  
   DeepBattlerには、HearthSimが開発したハースストーンデックトラッカー（HDT）のコンポーネントが含まれています。HDTおよびそのコンポーネントの全ての権利はHearthSimおよびその貢献者に帰属します。これはHearthSimによる所有権や承認を意味するものではありません。

4. **無保証**  
   本ソフトウェアは「現状のまま」提供されます。使用に起因する問題については一切の責任を負いません。

5. **派生作品**  
   本ソフトウェアを修正または基にして派生作品を作成する場合は、このライセンスを含め、その条項に従ってください。

6. **再配布**  
   本ソフトウェアまたはその派生作品を共有する場合は、このライセンスおよび著作権表示を保持してください。

DeepBattlerを使用することで、これらの条件に同意したことになります。

[William-Dic]  
[2024]
