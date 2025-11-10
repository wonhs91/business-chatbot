import axios from "axios";

type WidgetOptions = {
  baseUrl: string;
  title?: string;
  placeholder?: string;
  primaryColor?: string;
};

type ChatRole = "user" | "assistant" | "system";

interface ChatMessagePayload {
  role: ChatRole;
  content: string;
}

interface BackendMessage {
  role: ChatRole;
  content: string;
  timestamp?: string;
}

interface BackendResponse {
  session_id: string;
  messages: BackendMessage[];
  lead_captured: boolean;
  meeting_scheduled: boolean;
  suggested_slots?: string[] | null;
}

class ChatWidget {
  private options: Required<WidgetOptions>;
  private container: HTMLElement;
  private panel: HTMLElement;
  private messageList: HTMLElement;
  private input: HTMLTextAreaElement;
  private sendButton: HTMLButtonElement;
  private sessionId: string;
  private history: ChatMessagePayload[] = [];
  private isOpen = false;

  constructor(options: WidgetOptions) {
    if (!options.baseUrl) {
      throw new Error("Chat widget requires the backend baseUrl option.");
    }

    this.options = {
      title: options.title ?? "How can we help?",
      placeholder: options.placeholder ?? "Ask us anything...",
      primaryColor: options.primaryColor ?? "#2563eb",
      baseUrl: options.baseUrl,
    };

    this.sessionId = self.crypto?.randomUUID?.() ?? `session-${Date.now()}`;

    this.container = document.createElement("div");
    this.container.className = "bcw-container";

    this.panel = document.createElement("div");
    this.panel.className = "bcw-panel";

    const header = document.createElement("div");
    header.className = "bcw-header";
    header.textContent = this.options.title;

    const closeButton = document.createElement("button");
    closeButton.className = "bcw-close";
    closeButton.setAttribute("aria-label", "Close chat");
    closeButton.innerHTML = "&times;";
    closeButton.addEventListener("click", () => this.toggle(false));
    header.appendChild(closeButton);

    this.messageList = document.createElement("div");
    this.messageList.className = "bcw-messages";

    const composer = document.createElement("div");
    composer.className = "bcw-composer";

    this.input = document.createElement("textarea");
    this.input.placeholder = this.options.placeholder;
    this.input.rows = 2;
    this.input.addEventListener("keydown", (event) => {
      if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault();
        this.handleSend();
      }
    });

    this.sendButton = document.createElement("button");
    this.sendButton.className = "bcw-send";
    this.sendButton.textContent = "Send";
    this.sendButton.addEventListener("click", () => this.handleSend());

    composer.appendChild(this.input);
    composer.appendChild(this.sendButton);

    this.panel.appendChild(header);
    this.panel.appendChild(this.messageList);
    this.panel.appendChild(composer);

    const launcher = document.createElement("button");
    launcher.className = "bcw-launcher";
    launcher.setAttribute("aria-label", "Open chat");
    launcher.textContent = "Chat";
    launcher.addEventListener("click", () => this.toggle());

    this.container.appendChild(this.panel);
    this.container.appendChild(launcher);
  }

  mount(): void {
    this.injectStyles();
    document.body.appendChild(this.container);
  }

  toggle(force?: boolean): void {
    const desired = typeof force === "boolean" ? force : !this.isOpen;
    this.isOpen = desired;
    this.container.classList.toggle("bcw-open", this.isOpen);
    if (this.isOpen) {
      this.input.focus();
    }
  }

  private async handleSend(): Promise<void> {
    const text = this.input.value.trim();
    if (!text) return;

    this.appendMessage({ role: "user", content: text });
    this.input.value = "";
    this.setSending(true);

    try {
      const response = await axios.post<BackendResponse>(
        `${this.options.baseUrl.replace(/\/$/, "")}/api/chat`,
        {
          session_id: this.sessionId,
          message: { role: "user", content: text },
          history: this.history,
          metadata: { widget: "web" },
        },
        { timeout: 15000 }
      );

      const data = response.data;
      const assistantMessages = data.messages.filter(
        (msg) => msg.role === "assistant"
      );
      if (assistantMessages.length) {
        const latest = assistantMessages[assistantMessages.length - 1];
        this.appendMessage({ role: "assistant", content: latest.content });
      }

      if (data.suggested_slots?.length) {
        this.renderSuggestedSlots(data.suggested_slots);
      }
    } catch (error) {
      console.error("Chat send failed", error);
      this.appendMessage({
        role: "assistant",
        content:
          "I'm sorry, something went wrong. Please try again or reach us at contact@yourdomain.com.",
      });
    } finally {
      this.setSending(false);
    }
  }

  private appendMessage(message: ChatMessagePayload): void {
    this.history.push(message);

    const bubble = document.createElement("div");
    bubble.className = `bcw-bubble bcw-${message.role}`;
    bubble.textContent = message.content;
    this.messageList.appendChild(bubble);
    this.messageList.scrollTop = this.messageList.scrollHeight;
  }

  private renderSuggestedSlots(slots: string[]): void {
    const wrapper = document.createElement("div");
    wrapper.className = "bcw-slots";
    slots.forEach((slot) => {
      const button = document.createElement("button");
      button.className = "bcw-slot";
      button.textContent = new Date(slot).toLocaleString();
      button.addEventListener("click", () => {
        this.input.value = `Let's go with ${slot}`;
        this.handleSend();
      });
      wrapper.appendChild(button);
    });
    this.messageList.appendChild(wrapper);
    this.messageList.scrollTop = this.messageList.scrollHeight;
  }

  private injectStyles(): void {
    if (document.getElementById("bcw-styles")) return;
    const style = document.createElement("style");
    style.id = "bcw-styles";
    style.textContent = this.buildStyles();
    document.head.appendChild(style);
  }

  private buildStyles(): string {
    const primary = this.options.primaryColor;
    return `
      .bcw-container {
        position: fixed;
        bottom: 24px;
        right: 24px;
        z-index: 9999;
        font-family: 'Segoe UI', Arial, sans-serif;
      }

      .bcw-launcher {
        width: 56px;
        height: 56px;
        border-radius: 50%;
        border: none;
        background: ${primary};
        color: #fff;
        font-size: 24px;
        cursor: pointer;
        box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        transition: transform 0.2s ease;
      }

      .bcw-launcher:hover {
        transform: scale(1.05);
      }

      .bcw-panel {
        display: none;
        width: 320px;
        max-height: 480px;
        background: #fff;
        border-radius: 16px;
        box-shadow: 0 18px 40px rgba(0,0,0,0.15);
        overflow: hidden;
        flex-direction: column;
      }

      .bcw-open .bcw-panel {
        display: flex;
      }

      .bcw-open .bcw-launcher {
        display: none;
      }

      .bcw-header {
        background: ${primary};
        color: #fff;
        padding: 16px;
        font-weight: 600;
        display: flex;
        align-items: center;
        justify-content: space-between;
      }

      .bcw-close {
        background: transparent;
        border: none;
        color: inherit;
        font-size: 20px;
        cursor: pointer;
      }

      .bcw-messages {
        flex: 1;
        padding: 16px;
        overflow-y: auto;
        display: flex;
        flex-direction: column;
        gap: 12px;
      }

      .bcw-bubble {
        padding: 10px 14px;
        border-radius: 16px;
        line-height: 1.4;
        max-width: 80%;
        word-break: break-word;
      }

      .bcw-user {
        align-self: flex-end;
        background: ${primary};
        color: #fff;
        border-bottom-right-radius: 4px;
      }

      .bcw-assistant {
        align-self: flex-start;
        background: #f3f4f6;
        color: #111827;
        border-bottom-left-radius: 4px;
      }

      .bcw-composer {
        padding: 12px;
        border-top: 1px solid #e5e7eb;
        display: flex;
        gap: 8px;
      }

      .bcw-composer textarea {
        flex: 1;
        resize: none;
        border: 1px solid #d1d5db;
        border-radius: 8px;
        padding: 10px;
        font-family: inherit;
      }

      .bcw-send {
        background: ${primary};
        border: none;
        color: #fff;
        border-radius: 8px;
        padding: 0 16px;
        cursor: pointer;
        font-weight: 600;
      }

      .bcw-send[disabled] {
        opacity: 0.6;
        cursor: not-allowed;
      }

      .bcw-slots {
        display: flex;
        flex-direction: column;
        gap: 8px;
      }

      .bcw-slot {
        border: 1px solid ${primary};
        color: ${primary};
        background: transparent;
        border-radius: 12px;
        padding: 8px 12px;
        cursor: pointer;
        transition: background 0.2s ease;
      }

      .bcw-slot:hover {
        background: rgba(37, 99, 235, 0.1);
      }

      @media (max-width: 600px) {
        .bcw-container {
          bottom: 0;
          right: 0;
          left: 0;
          width: 100%;
        }

        .bcw-panel {
          width: 100%;
          height: 100vh;
          max-height: none;
          border-radius: 0;
        }
      }
    `;
  }

  private setSending(state: boolean): void {
    this.sendButton.disabled = state;
    this.input.disabled = state;
  }
}

declare global {
  interface Window {
    BusinessChatWidget?: {
      init: (options: WidgetOptions) => void;
    };
  }
}

export function init(options: WidgetOptions): void {
  const widget = new ChatWidget(options);
  widget.mount();
}

if (typeof window !== "undefined") {
  window.BusinessChatWidget = { init };
}
