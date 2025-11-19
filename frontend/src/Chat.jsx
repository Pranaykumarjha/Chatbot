import React, { useState, useEffect, useRef } from "react";
import axios from "axios";
import "./Chat.css";

const Chat = () => {
  const [message, setMessage] = useState("");
  const [chatLog, setChatLog] = useState([]);
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef(null);

  // Generate session ID if not present
  useEffect(() => {
    if (!localStorage.getItem("session_id")) {
      const newSessionId = `user_${Date.now()}`;
      localStorage.setItem("session_id", newSessionId);
    }
  }, []);

  // Scroll to bottom when chatLog updates
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chatLog]);

  const sendMessage = async () => {
    if (!message || loading) return;

    setChatLog((prev) => [...prev, { role: "User", text: message }]);
    setMessage("");
    setLoading(true);

    try {
      const sessionId = localStorage.getItem("session_id") || "user1";

      const res = await axios.post("http://127.0.0.1:5000/chat", {
        message,
        session_id: sessionId,
      });

      setChatLog((prev) => [
        ...prev,
        { role: "Bot", text: res.data.response },
      ]);
      localStorage.setItem("session_id", res.data.session_id);
    } catch (err) {
      console.error(err);
      setChatLog((prev) => [
        ...prev,
        { role: "Bot", text: "⚠ Error: Could not get response." },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === "Enter" && !loading) sendMessage();
  };

  return (
    <div className="chat-container">
      <h2 className="chat-title">RAG PDF Chatbot</h2>

      <div className="chat-log">
        {chatLog.map((msg, idx) => (
          <div
            key={idx}
            className={`chat-message ${msg.role === "User" ? "user" : "bot"}`}
          >
            {msg.text}
          </div>
        ))}

        {loading && <div className="chat-message bot typing">Bot is typing...</div>}
        <div ref={bottomRef} />
      </div>

      <div className="chat-input">
        <input
          type="text"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Type your message..."
          disabled={loading}
        />
        <button onClick={sendMessage} disabled={loading}>
          {loading ? "Sending..." : "Send"}
        </button>
      </div>
    </div>
  );
};

export default Chat;
