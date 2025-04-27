// Modal functionality
document.addEventListener("DOMContentLoaded", function () {
  // "Get Started" button opens login modal
  document
    .getElementById("get-started-btn")
    .addEventListener("click", function () {
      document.getElementById("login-modal").classList.remove("hidden");
    });

  // Login modal
  document.getElementById("login-btn").addEventListener("click", function () {
    document.getElementById("login-modal").classList.remove("hidden");
  });

  // Register modal open
  document
    .getElementById("register-btn")
    .addEventListener("click", function () {
      document.getElementById("register-modal").classList.remove("hidden");
    });

  // Common modal close logic (for both login & register)
  document.querySelectorAll(".modal-close").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".modal").forEach((modal) => {
        modal.classList.add("hidden");
      });
    });
  });

  // Close modals
  const modalCloseButtons = document.querySelectorAll(".modal-close");
  modalCloseButtons.forEach(function (button) {
    button.addEventListener("click", function () {
      document.querySelectorAll(".modal").forEach(function (modal) {
        modal.classList.add("hidden");
      });
    });
  });

  // Close modal when clicking outside
  const modals = document.querySelectorAll(".modal");
  modals.forEach(function (modal) {
    modal.addEventListener("click", function (e) {
      if (e.target === modal) {
        modal.classList.add("hidden");
      }
    });
  });

  // Smooth scroll for anchor links
  const anchorLinks = document.querySelectorAll('a[href^="#"]');
  anchorLinks.forEach(function (link) {
    link.addEventListener("click", function (e) {
      e.preventDefault();
      const targetId = this.getAttribute("href");
      const targetElement = document.querySelector(targetId);

      if (targetElement) {
        const offsetTop =
          targetElement.getBoundingClientRect().top + window.pageYOffset;
        window.scrollTo({
          top: offsetTop - 70,
          behavior: "smooth",
        });
      }
    });
  });

  // Feature card hover effect
  const featureCards = document.querySelectorAll(".feature-card");
  featureCards.forEach(function (card) {
    card.addEventListener("mouseenter", function () {
      this.querySelector("h3").classList.add("text-primary");
    });

    card.addEventListener("mouseleave", function () {
      this.querySelector("h3").classList.remove("text-primary");
    });
  });
});

function scrollToWithOffset(id, offset = 100) {
  const target = document.getElementById(id);
  if (target) {
    const top =
      target.getBoundingClientRect().top + window.pageYOffset - offset;
    window.scrollTo({ top, behavior: "smooth" });
  }
}

// Function to toggle modal visibility
function toggleModal(modalId) {
  const modal = document.getElementById(modalId);
  const modalContent = modal.querySelector('div');

  if (modal.classList.contains('hidden')) {
    // Show modal
    modal.classList.remove('hidden');
    setTimeout(() => {
      modal.classList.remove('opacity-0');
      modalContent.classList.remove('scale-95', 'opacity-0');
    }, 10);
  } else {
    // Hide modal
    modal.classList.add('opacity-0');
    modalContent.classList.add('scale-95', 'opacity-0');
    setTimeout(() => {
      modal.classList.add('hidden');
    }, 300);
  }
}

// Chat functionality
let currentChatId = null;
let chatInitialized = false;

// Function to start a new chat session
async function startChatSession() {
    try {
        console.log("Starting new chat session...");
        
        const response = await fetch('/api/chat/start', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ user_id: 'user_' + Date.now() })
        });
        
        const data = await response.json();
        if (data.status === 'success') {
            console.log("Chat session started successfully, chat ID:", data.chat_id);
            currentChatId = data.chat_id;
            chatInitialized = true;
            return true;
        } else {
            console.error("Failed to start chat session:", data.message);
            return false;
        }
    } catch (error) {
        console.error('Error starting chat session:', error);
        return false;
    }
}

// Function to retry API call with exponential backoff
async function retryFetch(url, options, maxRetries = 3) {
    let retries = 0;
    while (retries < maxRetries) {
        try {
            const response = await fetch(url, options);
            if (response.ok) {
                return response;
            }
        } catch (error) {
            console.warn(`Attempt ${retries + 1} failed:`, error);
        }
        
        // Exponential backoff
        const delay = Math.pow(2, retries) * 1000;
        await new Promise(resolve => setTimeout(resolve, delay));
        retries++;
    }
    
    // Last attempt
    return fetch(url, options);
}

// Function to send a message and get response
async function sendMessage() {
    const input = document.getElementById('chat-input');
    const message = input.value.trim();
    
    if (!message) return;
    
    // Clear input
    input.value = '';
    
    // Add user message to chat
    addMessageToChat(message, 'user');
    
    // If no active chat session, start one
    if (!currentChatId || !chatInitialized) {
        console.log("No active chat session, starting a new one...");
        const started = await startChatSession();
        if (!started) {
            addMessageToChat('Sorry, there was an error starting the chat session. Please try again later.', 'bot');
            return;
        }
    }
    
    try {
        // Create a new message element for the bot's response
        const chatContainer = document.getElementById('chat-container');
        const messageDiv = document.createElement('div');
        messageDiv.className = 'flex justify-start mb-6';
        
        const messageBubble = document.createElement('div');
        messageBubble.className = 'bg-gray-200 text-black rounded-lg py-3 px-4 max-w-[80%] shadow-sm';
        
        const messageText = document.createElement('p');
        messageText.className = 'font-medium';
        messageText.textContent = 'Thinking...';
        messageBubble.appendChild(messageText);
        
        const timestamp = document.createElement('p');
        timestamp.className = 'text-xs text-gray-500 mt-1';
        timestamp.textContent = 'Just now';
        messageBubble.appendChild(timestamp);
        
        messageDiv.appendChild(messageBubble);
        chatContainer.appendChild(messageDiv);
        
        // Scroll to bottom
        chatContainer.scrollTop = chatContainer.scrollHeight;
        
        console.log("Sending message to chat API...");
        // Make the API call with retry
        const response = await retryFetch('/api/chat/message', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                chat_id: currentChatId,
                user_id: 'user_' + Date.now(),
                message: message
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        // Clear the "Thinking..." text
        messageText.textContent = '';
        
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let accumulatedText = '';
        
        while (true) {
            const { value, done } = await reader.read();
            if (done) break;
            
            const chunk = decoder.decode(value);
            accumulatedText += chunk;
            
            // Update the message text with the accumulated response
            messageText.textContent = accumulatedText;
            
            // Scroll to bottom after each update
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }
        
    } catch (error) {
        console.error('Error sending message:', error);
        addMessageToChat(`Sorry, there was an error connecting to the server: ${error.message}. Please try again later.`, 'bot');
    }
}

// Function to add a message to the chat container
function addMessageToChat(message, sender) {
    const chatContainer = document.getElementById('chat-container');
    const messageDiv = document.createElement('div');
    
    messageDiv.className = `flex justify-${sender === 'user' ? 'end' : 'start'} mb-6`;
    
    const messageBubble = document.createElement('div');
    messageBubble.className = `${
        sender === 'user' 
            ? 'bg-primary text-white' 
            : 'bg-gray-200 text-black'
    } rounded-lg py-3 px-4 max-w-[80%] shadow-sm`;
    
    const messageText = document.createElement('p');
    messageText.className = 'font-medium';
    messageText.textContent = message;
    
    const timestamp = document.createElement('p');
    timestamp.className = 'text-xs text-gray-500 mt-1';
    timestamp.textContent = 'Just now';
    
    messageBubble.appendChild(messageText);
    messageBubble.appendChild(timestamp);
    messageDiv.appendChild(messageBubble);
    chatContainer.appendChild(messageDiv);
    
    // Scroll to bottom
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

// Initialize chat when modal is opened
document.addEventListener('DOMContentLoaded', function() {
    const chatbotModal = document.getElementById('chatbot-modal');
    const chatInput = document.getElementById('chat-input');
    const sendBtn = document.getElementById('send-btn');
    
    if (chatbotModal) {
        chatbotModal.addEventListener('click', async function(e) {
            if (e.target === this) {
                // Reset chat when modal is closed
                currentChatId = null;
                chatInitialized = false;
                const chatContainer = document.getElementById('chat-container');
                chatContainer.innerHTML = `
                    <div class="flex justify-start mb-6">
                        <div class="bg-gray-200 text-black rounded-lg py-3 px-4 max-w-[80%] shadow-sm">
                            <p class="font-medium">
                                Welcome to ADHDGuru! I'm here to help you with ADHD-related challenges. How can I assist you today?
                            </p>
                            <p class="text-xs text-gray-500 mt-1">Just now</p>
                        </div>
                    </div>
                `;
            }
        });
    }
    
    // Input field Enter key handler
    if (chatInput) {
        chatInput.addEventListener('keydown', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                sendMessage();
            }
        });
    }
    
    // Send button click handler
    if (sendBtn) {
        sendBtn.addEventListener('click', sendMessage);
    }
    
    // Initialize chat when document is ready
    if (chatbotModal && !chatbotModal.classList.contains('hidden')) {
        // If the chat modal is already open on page load, initialize it
        startChatSession();
    }
    
    // Handle feature card for chatbot
    const chatbotFeatureCard = document.querySelector('.feature-card[onclick="toggleModal(\'chatbot-modal\')"]');
    if (chatbotFeatureCard) {
        chatbotFeatureCard.addEventListener('click', function() {
            // Initialize chat when opening modal via feature card
            if (!chatInitialized) {
                setTimeout(() => startChatSession(), 500);
            }
        });
    }
});

// Sample chat data (in a real app, this would come from a database)
const chatData = {
  "sleep-tracking": [
    { type: "user", text: "Hello, I need help with my sleep tracking." },
    {
      type: "bot",
      text: "Hi there! I'd be happy to help you with sleep tracking. What specific concerns do you have about your sleep patterns?",
      hasBreakdown: true,
    },
    {
      type: "user",
      text: "I've been having trouble falling asleep. Can you suggest some strategies?",
    },
    {
      type: "bot",
      text: "Of course! Here are some strategies that might help:<ul class='list-disc pl-6 mt-3 space-y-2'><li>Establish a regular sleep schedule</li><li>Create a relaxing bedtime routine</li><li>Limit screen time before bed</li><li>Keep your bedroom cool and dark</li></ul>Would you like more details on any of these?",
    },
  ],
  "diet-recommendations": [
    { type: "user", text: "I need help with my diet plan" },
    {
      type: "bot",
      text: "I'd be happy to help with your diet plan. What are your dietary goals?",
      hasBreakdown: true,
    },
    {
      type: "user",
      text: "I want to reduce sugar intake and eat more protein",
    },
    {
      type: "bot",
      text: "That's a great goal! Here are some suggestions:<ul class='list-disc pl-6 mt-3 space-y-2'><li>Replace sugary drinks with water or tea</li><li>Include lean protein at every meal</li><li>Read food labels for hidden sugars</li><li>Try Greek yogurt for a high-protein snack</li></ul>",
    },
  ],
  "exercise-routine": [
    { type: "user", text: "Can you recommend a home workout routine?" },
    {
      type: "bot",
      text: "Absolutely! What equipment do you have available at home?",
    },
    { type: "user", text: "Just a yoga mat and some resistance bands" },
    {
      type: "bot",
      text: "Perfect! Here's a 20-minute routine you can try:<ul class='list-disc pl-6 mt-3 space-y-2'><li>5-minute warm-up with dynamic stretches</li><li>Circuit: 30 seconds each of squats, push-ups, resistance band rows</li><li>Rest 1 minute, repeat circuit 3 times</li><li>5-minute cool down stretch</li></ul>",
      hasBreakdown: true,
    },
  ],
};

// Function to load chat messages
function loadChat(chatId) {
  const chatContainer = document.getElementById("chat-container");
  
  // Add fade-out animation before clearing
  chatContainer.classList.add('animate-fade-out');
  
  setTimeout(() => {
    chatContainer.innerHTML = ""; // Clear existing messages
    
    // Make previously selected chat item normal style
    document.querySelectorAll(".chat-history-item").forEach((item) => {
      item.classList.remove("bg-secondary");
      item.classList.add("bg-gray-200");
    });

    // Highlight the selected chat with transition
    const selectedItem = document.querySelector(`[data-chat-id="${chatId}"]`);
    if (selectedItem) {
      selectedItem.classList.remove("bg-gray-200");
      selectedItem.classList.add("bg-secondary", "transition-colors", "duration-300");
    }

    // Get the chat messages
    const messages = chatData[chatId];
    if (!messages) return;
    
    // Remove fade-out and add fade-in to container
    chatContainer.classList.remove('animate-fade-out');
    chatContainer.classList.add('animate-fade-in');

    // Add each message with a slight delay for animation
    messages.forEach((message, index) => {
      setTimeout(() => {
        const messageDiv = document.createElement("div");
        messageDiv.className = `flex justify-${
          message.type === "user" ? "end" : "start"
        } mb-6 opacity-0 transition-opacity duration-300`;

        const messageBubble = document.createElement("div");
        messageBubble.className =
          message.type === "user"
            ? "bg-primary text-white rounded-lg rounded-tr-sm shadow-lg max-w-lg px-6 py-4 transform transition-transform duration-300 scale-95"
            : "text-black bg-gray-200 rounded-lg rounded-tl-sm shadow-lg max-w-lg px-6 py-4 transform transition-transform duration-300 scale-95";
        messageBubble.innerHTML = message.text;

        messageDiv.appendChild(messageBubble);
        chatContainer.appendChild(messageDiv);

        // Add breakdown button if needed
        if (message.hasBreakdown) {
          const breakdownDiv = document.createElement("div");
          breakdownDiv.className = "flex justify-start mb-4 opacity-0 transition-opacity duration-300";

          const breakdownBtn = document.createElement("button");
          breakdownBtn.className =
            "text-xs text-primary bg-white px-4 py-2 rounded border border-primary hover:bg-primary hover:text-secondary transition-all duration-200 shadow-md";
          breakdownBtn.textContent = "Breakdown";
          breakdownBtn.onclick = () =>
            alert("Showing breakdown details for this response");

          breakdownDiv.appendChild(breakdownBtn);
          chatContainer.appendChild(breakdownDiv);
          
          // Animate breakdown button after short delay
          setTimeout(() => {
            breakdownDiv.classList.remove("opacity-0");
            breakdownDiv.classList.add("opacity-100");
          }, 100);
        }

        // Animate message appearance
        setTimeout(() => {
          messageDiv.classList.remove("opacity-0");
          messageDiv.classList.add("opacity-100");
          messageBubble.classList.remove("scale-95");
          messageBubble.classList.add("scale-100");
        }, 50);

        // Scroll to the bottom
        chatContainer.scrollTop = chatContainer.scrollHeight;
      }, index * 200); // Slightly faster staggered appearance
    });
    
    // Remove fade-in class after animation completes
    setTimeout(() => {
      chatContainer.classList.remove('animate-fade-in');
    }, 500);
    
  }, 300); // Wait for fade-out animation to complete
}

// Add event listeners to chat history items
document.querySelectorAll(".chat-history-item").forEach((item) => {
  item.addEventListener("click", function() {
    const chatId = this.getAttribute("data-chat-id");
    
    // Add ripple effect on click
    const ripple = document.createElement("span");
    ripple.classList.add("ripple-effect");
    this.appendChild(ripple);
    
    // Remove ripple after animation
    setTimeout(() => {
      ripple.remove();
    }, 600);
    
    loadChat(chatId);
  });
});

// Add CSS for animations if it doesn't exist already
if (!document.getElementById("chat-animations-css")) {
  const styleSheet = document.createElement("style");
  styleSheet.id = "chat-animations-css";
  styleSheet.textContent = `
    @keyframes fadeIn {
      from { opacity: 0; }
      to { opacity: 1; }
    }
    @keyframes fadeOut {
      from { opacity: 1; }
      to { opacity: 0; }
    }
    .animate-fade-in {
      animation: fadeIn 0.3s ease-in-out forwards;
    }
    .animate-fade-out {
      animation: fadeOut 0.3s ease-in-out forwards;
    }
    .ripple-effect {
      position: absolute;
      border-radius: 50%;
      background: rgba(255, 255, 255, 0.7);
      transform: scale(0);
      animation: ripple 0.6s linear;
      pointer-events: none;
    }
    @keyframes ripple {
      to {
        transform: scale(4);
        opacity: 0;
      }
    }
  `;
  document.head.appendChild(styleSheet);
}

// Load the first chat by default
loadChat("sleep-tracking");

// Event listeners for chat button
document.addEventListener('DOMContentLoaded', () => {
    const openChatBtn = document.getElementById('open-chatbot-btn');
    if (openChatBtn) {
        openChatBtn.addEventListener('click', () => toggleModal('chatbot-modal'));
    }

    // Close modal when clicking outside
    const modal = document.getElementById('chatbot-modal');
    if (modal) {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                toggleModal('chatbot-modal');
            }
        });
    }

    // Debug logging for chat initialization
    console.log('Chat initialization started');
    
    // Test backend connectivity
    fetch('/api/chat/start', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ user_id: 'test_user' })
    })
    .then(response => response.json())
    .then(data => {
        console.log('Backend connection successful:', data);
    })
    .catch(error => {
        console.error('Backend connection failed:', error);
    });
});
