


```mermaid
---
title: Enchiridion
---

classDiagram
    class Message {
        +str user_name
        +str text
        +bool is_user
        +__init__(user_name: str, text: str, is_user: bool)
        +__str__()
    }

    class Tool {
        +str name
        +str description
        +callable function
        +__init__(name: str, description: str, function: callable)
    }

    class Agent {
        +str name
        +str description
        +str prompt
        +List[Tool] tools
        +__init__(name: str, description: str, prompt: str, tools: List[Tool])
    }

    class AgentManager {
        +str config_file
        +Dict[str, Agent] agents
        +__init__(config_file: str)
        +load_agents()
        +get_agent(name: str) -> Agent
        +list_agents() -> List[str]
    }

    class AgentCard {
        +Agent agent
        +callable on_click
        +__init__(agent: Agent, on_click)
        +build()
    }

    class AgentModal {
        +Agent agent
        +callable on_close
        +__init__(agent: Agent, on_close)
        +build()
        -create_tool_card(tool: Tool)
    }

    class AgentGallery {
        +AgentManager agent_manager
        +bool modal_visible
        +Agent selected_agent
        +__init__(agent_manager: AgentManager)
        +build()
        +open_agent_modal(agent: Agent)
        +close_agent_modal(_)
    }

    class ChatApp {
        +AgentManager agent_manager
        +Agent current_agent
        +ListView chat_view
        +TextField new_message
        +IconButton send_button
        +Dropdown agent_dropdown
        +AgentGallery agent_gallery
        +__init__(agent_manager: AgentManager)
        +build()
        +change_agent(e)
        +send_message(e)
        +add_message(message: Message)
        +render_message(message: Message)
        +get_ai_response()
    }

    AgentManager "1" -- "*" Agent : manages
    Agent "1" -- "*" Tool : has
    AgentCard "1" -- "1" Agent : displays
    AgentModal "1" -- "1" Agent : displays
    AgentGallery "1" -- "1" AgentManager : uses
    AgentGallery "1" -- "*" AgentCard : contains
    AgentGallery "1" -- "0..1" AgentModal : shows
    ChatApp "1" -- "1" AgentManager : uses
    ChatApp "1" -- "1" AgentGallery : contains
    ChatApp "1" -- "*" Message : manages
    ChatApp ..> AgentCard : creates
    ChatApp ..> AgentModal : creates
    main --> ChatApp : creates
    main --> AgentManager : creates
    ```
