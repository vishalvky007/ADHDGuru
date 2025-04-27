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

// // Function to toggle modal visibility
// function toggleModal(modalId, event) {
//   const modal = document.getElementById(modalId);
//   if (!modal) return;
  
//   const modalContent = modal.querySelector('div');
  
//   if (modal.classList.contains('hidden')) {
//     // Show modal
//     modal.classList.remove('hidden');
//     setTimeout(() => {
//       modal.classList.remove('opacity-0');
//       modalContent.classList.remove('scale-95', 'opacity-0');
      
//       // Initialize chat session when opening the chatbot modal
//       if (modalId === 'chatbot-modal') {
//         if (!chatInitialized && typeof startChatSession === 'function') {
//           startChatSession().catch(err => {
//             console.error("Failed to start chat session:", err);
//           });
//         }
//       }
//     }, 10);
//   } else {
//     // Don't hide chatbot modal if that's what was clicked
//     // Only proceed with hiding other modals
//     if (modalId !== 'chatbot-modal' || event && event.explicitClose) {
//       // Hide modal
//       modal.classList.add('opacity-0');
//       modalContent.classList.add('scale-95', 'opacity-0');
//       setTimeout(() => {
//         modal.classList.add('hidden');
//       }, 300);
//     }
//   }
// }

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
        chatbotModal.addEventListener('click', function(e) {
            // Only close if clicking on backdrop, not modal content
            if (e.target === chatbotModal && e.target !== e.currentTarget.querySelector('.modal-content')) {
                // Create custom event with explicit close flag
                const customEvent = new Event('click');
                customEvent.explicitClose = true;
                toggleModal('chatbot-modal', customEvent);
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
    
    // Handle feature card for chatbot
    const chatbotFeatureCard = document.querySelector('.feature-card[onclick="toggleModal(\'chatbot-modal\')"]');
    if (chatbotFeatureCard) {
        chatbotFeatureCard.addEventListener('click', function(e) {
            e.preventDefault();
            toggleModal('chatbot-modal');
            // Initialize chat when opening modal
            if (!chatInitialized) {
                setTimeout(() => startChatSession(), 300);
            }
        });
    }
});

// Event listeners for chat button
document.addEventListener('DOMContentLoaded', () => {
    const openChatBtn = document.getElementById('open-chatbot-btn');
    if (openChatBtn) {
        openChatBtn.addEventListener('click', () => toggleModal('chatbot-modal'));
    }
    
    // Test backend connectivity - optional, can be removed if not needed
    console.log('Chat initialization started');
});

