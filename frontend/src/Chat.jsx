import React, { useState, useEffect, useRef } from "react";
import axios from "axios";
import "./Chat.css"; // We'll add styles here

const Chat = () => {
  const [message, setMessage] = useState("");
  const [chatLog, setChatLog] = useState([]);
  const bottomRef = useRef(null);

  const sendMessage = async () => {
    if (!message) return;

    // Add user message
    setChatLog((prev) => [...prev, { role: "User", text: message }]);

    try {
      const res = await axios.post("http://127.0.0.1:5000/chat", {
        message,
        session_id: "user1"
      });
      // Add bot response
      setChatLog((prev) => [...prev, { role: "Bot", text: res.data.response }]);
      setMessage("");
    } catch (err) {
      console.error(err);
      setChatLog((prev) => [...prev, { role: "Bot", text: "Error: Could not get response." }]);
    }
  };

  // Auto scroll to bottom
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chatLog]);

  const handleKeyPress = (e) => {
    if (e.key === "Enter") sendMessage();
  };

  return (
    <div className="chat-container">
      <div className="chat-log">
        {chatLog.map((msg, idx) => (
          <div
            key={idx}
            className={`chat-message ${msg.role === "User" ? "user" : "bot"}`}
          >
            {msg.text}
          </div>
        ))}
        <div ref={bottomRef} />
      </div>
      <div className="chat-input">
        <input
          type="text"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Type your message..."
        />
        <button onClick={sendMessage}>Send</button>
      </div>
    </div>
  );
};

export default Chat;
