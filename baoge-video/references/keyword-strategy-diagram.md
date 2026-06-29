# 关键词编辑策略逻辑架构

> 本文档用 Mermaid 图展示宝哥视频项目中关键词从分镜方案到各平台搜索的完整决策流程。

## 一、总体决策流程

```mermaid
flowchart TD
    Start(["分镜方案表<br/>关键词列"]) --> A{关键词内容<br/>的地域属性？}
    
    A -->|国外企业/人物/场景| B["优先平台：YouTube → Pexels → B站 → 抖音"]
    A -->|国内企业/人物/场景| C["优先平台：抖音 → B站 → YouTube → Pexels"]
    A -->|通用科技/工业| D["优先平台：抖音 → B站 → YouTube → Pexels/Mixkit"]
    
    B --> E{平台实拍<br/>还是素材网站？}
    C --> E
    D --> E
    
    E -->|平台实拍| F["中文关键词直接搜索<br/>(分镜方案关键词)"]
    E -->|素材网站| G["英文实体场景词<br/>(翻译+转换)"]
    
    F --> H{搜到了吗？}
    G --> I{搜到了吗？}
    
    H -->|是| J["预筛选 → 下载 → 验收"]
    H -->|否| K["切换备选关键词<br/>(分镜方案备选方案列)"]
    
    I -->|是| L["标签排除 → 缩略图AI分析<br/>→ 下载 → 验收"]
    I -->|否| M["后缀'素材'备选<br/>(中文关键词)"]
    
    K --> H
    M --> N{搜到了吗？}
    N -->|是| L
    N -->|否| O["更宽泛的英文场景词"]
    O --> I
```

## 二、关键词地域判断树

```mermaid
flowchart LR
    Sub1["关键词内容"] --> Q1{"涉及国外<br/>企业/人物/场景？"}
    
    Q1 -->|是：英伟达、黄仁勋、台积电<br/>硅谷、华尔街| R1["YouTube优先"]
    Q1 -->|否| Q2{"涉及国内<br/>企业/人物/场景？"}
    
    Q2 -->|是：比亚迪、宁德时代、华为| R2["抖音优先"]
    Q2 -->|否：芯片制造、光纤、数据中心| R3["按通用流程"]
    
    R1 --> S1["实拍：中文'英伟达 工厂'<br/>素材网站：英文'NVIDIA factory'"]
    R2 --> S2["实拍：中文'比亚迪 工厂'<br/>素材网站：中文或英文"]
    R3 --> S3["实拍：中文'芯片 制造'<br/>素材网站：英文'chip manufacturing'"]
```

## 三、关键词备选层级（降级路径）

```mermaid
flowchart TD
    L1["🥇 第一优先<br/>分镜方案关键词<br/>（人工填写，针对性最强）"]
    L2["🥈 第二优先<br/>备选关键词<br/>（分镜方案备选方案列）"]
    L3["🥉 第三优先<br/>后缀'素材'<br/>（中文关键词+素材）"]
    L4["🏅 第四优先<br/>实体场景词<br/>（英文，搜物理环境）"]
    L5["🎯 第五优先<br/>更宽泛场景词<br/>（扩大搜索范围）"]
    
    L1 -->|搜不到| L2
    L2 -->|搜不到| L3
    L3 -->|搜不到| L4
    L4 -->|搜不到| L5
```

## 四、平台搜索顺序（按地域）

```mermaid
flowchart TD
    subgraph 国外关键词
        A1["YouTube"] --> A2["Pexels/Pixabay"] --> A3["B站"] --> A4["抖音"]
    end
    
    subgraph 国内关键词
        B1["抖音"] --> B2["B站"] --> B3["YouTube"] --> B4["Pexels/Pixabay"]
    end
    
    subgraph 通用关键词
        C1["抖音"] --> C2["B站"] --> C3["YouTube"] --> C4["Pexels/Pixabay/Mixkit"]
    end
```

## 五、关键词语言映射

```mermaid
flowchart LR
    subgraph 分镜方案
        KW["中文关键词<br/>半导体 工厂 航拍"]
    end
    
    subgraph 平台实拍
        KW -->|直接使用| CN["中文搜索<br/>'半导体 工厂 航拍'"]
    end
    
    subgraph 素材网站
        KW -->|翻译转换| EN["英文搜索<br/>'semiconductor factory aerial'"]
        EN -->|搜不到| CN2["中文+素材<br/>'半导体素材'"]
    end
```

## 六、完整决策树（含所有分支）

```mermaid
flowchart TD
    Input(["分镜方案关键词"]) --> Step1["判断地域属性"]
    
    Step1 --> Step1a{"国外内容？"}
    Step1a -->|是| Step2a["平台顺序：YouTube → Pexels → B站 → 抖音"]
    Step1a -->|否| Step1b{"国内内容？"}
    
    Step1b -->|是| Step2b["平台顺序：抖音 → B站 → YouTube → Pexels"]
    Step1b -->|否| Step2c["平台顺序：抖音 → B站 → YouTube → Pexels/Mixkit"]
    
    Step2a --> Step3{"哪个平台类型？"}
    Step2b --> Step3
    Step2c --> Step3
    
    Step3 -->|平台实拍| Step4a["中文关键词搜索"]
    Step3 -->|素材网站| Step4b["英文实体场景词搜索"]
    
    Step4a --> Result1{"有结果？"}
    Result1 -->|✅ 有| Done1["预筛选 → 下载 → 验收"]
    Result1 -->|❌ 无| Fallback1["切换备选关键词"]
    Fallback1 --> Step4a
    
    Step4b --> Result2{"有结果？"}
    Result2 -->|✅ 有| Done2["标签排除 → 缩略图AI分析 → 下载 → 验收"]
    Result2 -->|❌ 无| Fallback2["后缀'素材'备选"]
    Fallback2 --> Result3{"有结果？"}
    Result3 -->|✅ 有| Done2
    Result3 -->|❌ 无| Fallback3["更宽泛英文场景词"]
    Fallback3 --> Step4b
```

---

> 本图对应的完整规则文档：`references/keyword-rules.md`
