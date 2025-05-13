let mediaRecorder;
let audioChunks = [];
let audioWs;
let textWs;
let isRecording = false;
let audioContext;
let audioStream;
let audioBuffer = [];

// Chat state
let currentChatId = null;
let userId = localStorage.getItem('userId') || crypto.randomUUID();
localStorage.setItem('userId', userId);

// Add at the top with other global variables
let currentCommandContext = null;

// UI Elements
const orb = document.getElementById('orb');
const statusText = document.getElementById('status');
const chatMessages = document.getElementById('chat-messages');
const chatList = document.getElementById('chat-list');
const newChatButton = document.getElementById('new-chat-button');
const currentChatTitle = document.getElementById('current-chat-title');
const emailPreviewSubject = document.getElementById('email-preview-subject');
const emailPreviewBody = document.getElementById('email-preview-body');
const emailInput = document.getElementById('email-input');
const emailDialog = document.getElementById('email-dialog');
const dialogOverlay = document.getElementById('dialog-overlay');
const emailCancelButton = document.getElementById('email-cancel-button');
const emailSendButton = document.getElementById('email-send-button');

function updateOrbState(state) {
    // Remove all state classes
    orb.classList.remove('recording', 'processing', 'speaking');
    
    // Add the new state class if provided
    if (state) {
        orb.classList.add(state);
    }
}

function updateStatus(text) {
    statusText.textContent = text;
}

function showTranscription(transcript) {
    console.log('Showing transcription:', transcript);
    const transcriptElement = document.getElementById('transcript');
    const transcriptContainer = document.getElementById('transcript-container');
    
    if (transcriptElement && transcriptContainer) {
        if (transcript) {
            transcriptElement.textContent = transcript;
            transcriptContainer.classList.add('visible');
            console.log('Transcription container made visible');
        } else {
            transcriptElement.textContent = 'No transcription available';
            transcriptContainer.classList.remove('visible');
        }
    }
}

function showJarvisResponse(response) {
    console.log('Showing JARVIS response:', response);
    const responseElement = document.getElementById('command-response');
    const container = document.getElementById('command-container');
    
    if (response) {
        // Try to get response from different possible locations
        let responseText;
        if (typeof response === 'string') {
            responseText = response;
        } else if (response.response) {
            // Check top-level response first
            responseText = response.response;
        } else if (response.command_data?.response) {
            // Then check command_data.response
            responseText = response.command_data.response;
        } else {
            responseText = 'No response available';
        }
        
        console.log('Setting JARVIS response text:', responseText);
        responseElement.textContent = responseText;
        
        // Make sure the container is visible
        container.style.display = 'flex';
        container.classList.add('visible');
        console.log('Command container made visible');
        
        // Update orb state
        updateOrbState('speaking');
        
        // Reset orb state after 2 seconds
        setTimeout(() => {
            updateOrbState(null);
            updateStatus('Ready to record');
        }, 2000);
    } else {
        console.log('No JARVIS response to show');
        responseElement.textContent = 'No response available';
    }
}

function showError(message) {
    const errorElement = document.getElementById('error-message');
    errorElement.textContent = message;
    errorElement.classList.add('visible');
    setTimeout(() => {
        errorElement.classList.remove('visible');
    }, 5000);
}

// Initialize chat
async function initializeChat() {
    // Create a new chat session
    await createNewChat();
    // Load existing chats
    await loadChatSessions();
}

async function createNewChat() {
    try {
        const response = await fetch('http://localhost:8000/api/create-chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                user_id: getUserId(),
                title: 'New Chat'
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const chat = await response.json();
        
        // Add the new chat to the list at the top
        addChatToList(chat);
        
        // Switch to the new chat
        document.querySelectorAll('.chat-item').forEach(item => {
            item.classList.remove('active');
        });
        const newChatItem = document.querySelector(`[data-chat-id="${chat.chat_id}"]`);
        if (newChatItem) {
            newChatItem.classList.add('active');
        }
        
        // Clear the chat messages
        const chatMessages = document.getElementById('chat-messages');
        if (chatMessages) {
            chatMessages.innerHTML = '';
        }
        
        // Update current chat ID and title
        currentChatId = chat.chat_id;
        const currentChatTitle = document.getElementById('current-chat-title');
        if (currentChatTitle) {
            currentChatTitle.textContent = chat.title || 'New Chat';
        }
        
        return chat.chat_id;
    } catch (error) {
        console.error('Error creating new chat:', error);
        showError('Failed to create new chat');
        return null;
    }
}

async function loadChatSessions() {
    try {
        const userId = getUserId(); // Get the current user ID
        const response = await fetch(`http://localhost:8000/api/list-chats?user_id=${userId}`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const chats = await response.json();
        const chatList = document.getElementById('chat-list');
        if (!chatList) {
            console.error('Chat list element not found');
            return;
        }
        chatList.innerHTML = ''; // Clear existing chats
        
        // Add each chat to the list
        chats.forEach(chat => {
            addChatToList(chat);
        });
        
        // If no chats exist, create a new one
        if (chats.length === 0) {
            createNewChat();
        }
    } catch (error) {
        console.error('Error loading chat sessions:', error);
        showError('Failed to load chat sessions');
    }
}

// Helper function to get or create user ID
function getUserId() {
    let userId = localStorage.getItem('userId');
    if (!userId) {
        userId = crypto.randomUUID();
        localStorage.setItem('userId', userId);
    }
    return userId;
}

function addChatToList(chat) {
    const chatList = document.getElementById('chat-list');
    if (!chatList) {
        console.error('Chat list element not found');
        return;
    }
    const chatItem = document.createElement('div');
    chatItem.className = 'chat-item';
    chatItem.dataset.chatId = chat.chat_id;
    
    // Create chat item content
    chatItem.innerHTML = `
        <div class="chat-item-content">
            <span class="chat-item-title">${chat.title || 'New Chat'}</span>
            <button class="delete-chat-button" title="Delete chat">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M3 6h18M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                </svg>
            </button>
        </div>
    `;
    
    // Add click handler for the chat item
    chatItem.addEventListener('click', async (e) => {
        // Don't switch chats if clicking delete button
        if (e.target.closest('.delete-chat-button')) {
            return;
        }
        
        // Remove active class from all chats
        document.querySelectorAll('.chat-item').forEach(item => {
            item.classList.remove('active');
        });
        
        // Add active class to clicked chat
        chatItem.classList.add('active');
        
        // Load chat messages
        await loadChatMessages(chat.chat_id);
    });
    
    // Add click handler for delete button
    const deleteButton = chatItem.querySelector('.delete-chat-button');
    deleteButton.addEventListener('click', async (e) => {
        e.stopPropagation(); // Prevent chat selection
        
        if (confirm('Are you sure you want to delete this chat?')) {
            await deleteChat(chat.chat_id);
        }
    });
    
    // Insert at the beginning of the list to maintain newest-first order
    if (chatList.firstChild) {
        chatList.insertBefore(chatItem, chatList.firstChild);
    } else {
        chatList.appendChild(chatItem);
    }
}

async function switchChat(chatId) {
    try {
        const response = await fetch(`http://localhost:8000/api/get-chat/${chatId}`);
        if (!response.ok) throw new Error('Failed to load chat');
        
        const chat = await response.json();
        currentChatId = chatId;
        currentChatTitle.textContent = chat.title;
        
        // Update active state in chat list
        document.querySelectorAll('.chat-item').forEach(item => {
            item.classList.remove('active');
        });
        document.querySelector(`.chat-item[data-chat-id="${chatId}"]`)?.classList.add('active');
        
        // Load messages
        await loadChatMessages(chatId);
    } catch (error) {
        console.error('Error switching chat:', error);
        showError('Failed to load chat');
    }
}

async function loadChatMessages(chatId) {
    try {
        const response = await fetch(`http://localhost:8000/api/get-chat-messages/${chatId}`);
        if (!response.ok) throw new Error('Failed to load messages');
        
        const messages = await response.json();
        const chatMessages = document.getElementById('chat-messages');
        if (chatMessages) {
            chatMessages.innerHTML = ''; // Clear existing messages
            
            messages.forEach(message => {
                // Convert the message format to match what addMessageToChat expects
                const formattedMessage = {
                    type: message.query ? 'user' : 'assistant',
                    query: message.query || '',
                    response: message.response || '',
                    timestamp: message.timestamp,
                    content: message.query || message.response || '' // For backward compatibility
                };
                addMessageToChat(formattedMessage);
            });
            
            // Scroll to bottom
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }
    } catch (error) {
        console.error('Error loading messages:', error);
        showError('Failed to load messages');
    }
}

function addMessageToChat(message) {
    const messageElement = document.createElement('div');
    messageElement.className = `message ${message.type}`;
    
    // Get the content from either query or response field
    let content = '';
    if (message.type === 'user') {
        content = message.query || '';
    } else if (message.type === 'assistant') {
        content = message.response || '';
    }
    
    // Format the timestamp
    const time = new Date(message.timestamp);
    
    messageElement.innerHTML = `
        <div class="message-content">${content}</div>
        <div class="message-time">${formatTime(time)}</div>
    `;
    
    const chatMessages = document.getElementById('chat-messages');
    if (chatMessages) {
        chatMessages.appendChild(messageElement);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
}

function formatTime(date) {
    if (!date) return '';
    
    try {
        if (typeof date === 'string') {
            date = new Date(date);
        }
        // Check if date is valid
        if (isNaN(date.getTime())) {
            return '';
        }
        return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    } catch (error) {
        console.error('Error formatting time:', error);
        return '';
    }
}

// Event Listeners
newChatButton.addEventListener('click', createNewChat);

// WebSocket message handling
function handleWebSocketMessage(response) {
    console.log('Handling WebSocket message:', response);
    
    switch(response.type) {
        case 'transcription':
            if (response.error) {
                showError(response.error);
                updateStatus(`Error: ${response.error}`);
                updateOrbState(null);
            } else {
                showTranscription(response.transcription);
                addMessageToChat({
                    type: 'user',
                    query: response.transcription,
                    timestamp: new Date().toISOString()
                });
                updateStatus('Processing command...');
                updateOrbState('processing');
            }
            break;
            
        case 'jarvis':
            if (response.error) {
                showError(response.error);
                updateStatus(`Error: ${response.error}`);
                updateOrbState(null);
                // If we get an error, hide the email dialog
                if (response.error.includes('email') || response.error.includes('context')) {
                    hideEmailDialog();
                }
            } else {
                // Store the command context if it requires follow-up
                if (response.command_data?.requires_followup) {
                    console.log('Storing command context for follow-up:', response.command_data);
                    currentCommandContext = response.command_data;
                    
                    // Only show email dialog for initial email command
                    // Don't show if we already have a 'to' address (meaning email was just sent)
                    if (response.command_data?.followup_context?.context?.type === 'email_input' && 
                        !response.command_data?.parameters?.to && 
                        !emailDialog.classList.contains('visible')) {  // Extra check to prevent showing if already visible
                        console.log('Showing email dialog for initial follow-up:', response.command_data);
                        showEmailDialog(response.command_data.followup_context.context.current_draft);
                    }
                }
                
                // Handle the response
                if (response.response) {
                    showTranscription(response.response);
                }
                
                // Add assistant message to chat
                addMessageToChat({
                    type: 'assistant',
                    response: response.response || response.command_data?.response || 'No response available',
                    timestamp: new Date().toISOString()
                });
                
                // Update status and orb
                updateStatus('Ready to record');
                updateOrbState('speaking');
                setTimeout(() => {
                    updateOrbState(null);
                }, 2000);
            }
            break;
            
        case 'error':
            console.error('Received error from server:', response.error);
            showError(response.error);
            updateStatus(`Error: ${response.error}`);
            updateOrbState(null);
            
            // If we get an error about invalid context or email, hide the dialog
            if (response.error.includes('context') || response.error.includes('email')) {
                hideEmailDialog();
            }
            break;
    }
}

async function storeMessage(chatId, content, type) {
    if (!chatId || !content || !type) {
        console.error('Missing required message data:', { chatId, content, type });
        return;
    }

    try {
        const response = await fetch('http://localhost:8000/api/store-message', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                chat_id: chatId,
                user_id: userId,
                content: content,
                type: type
            })
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Failed to store message');
        }

        const data = await response.json();
        if (data.status !== 'success') {
            throw new Error('Message storage failed');
        }
    } catch (error) {
        console.error('Error storing message:', error);
        // Don't show error to user for message storage failures
        // as it would be too disruptive to the chat experience
    }
}

// Function to show email dialog
function showEmailDialog(draft) {
    console.log('Showing email dialog with draft:', draft);
    if (!draft) {
        console.error('No draft provided for email dialog');
        return;
    }
    
    // Update preview with draft content
    emailPreviewSubject.textContent = draft.subject || 'No Subject';
    emailPreviewBody.textContent = draft.body || '';
    
    // Clear any previous input
    emailInput.value = '';
    
    // Show the dialog
    emailDialog.classList.add('visible');
    dialogOverlay.classList.add('visible');
    
    // Focus the email input
    emailInput.focus();
    
    // Ensure text WebSocket is connected
    if (!textWs || textWs.readyState !== WebSocket.OPEN) {
        console.log('Connecting text WebSocket for email dialog');
        connectTextWebSocket();
    }
}

// Connect only the text WebSocket
async function connectTextWebSocket() {
    textWs = new WebSocket('ws://localhost:8000/ws/text');
    
    textWs.onopen = () => {
        console.log('Text WebSocket connection established');
    };
    
    textWs.onmessage = (event) => {
        console.log('Received text WebSocket message:', event.data);
        try {
            const response = JSON.parse(event.data);
            handleWebSocketMessage(response);
        } catch (error) {
            console.error('Error processing text WebSocket message:', error);
        }
    };
    
    textWs.onerror = (error) => {
        console.error('Text WebSocket error:', error);
        showError('Error connecting to server');
    };
    
    textWs.onclose = () => {
        console.log('Text WebSocket connection closed');
    };
}

// Update WebSocket connection to only handle audio
async function connectWebSockets() {
    // Connect to audio WebSocket
    audioWs = new WebSocket('ws://localhost:8000/ws/audio');
    
    audioWs.onopen = () => {
        console.log('Audio WebSocket connection established');
        updateStatus('Ready to record');
    };
    
    audioWs.onmessage = (event) => {
        console.log('Received audio WebSocket message:', event.data);
        try {
            const response = JSON.parse(event.data);
            handleWebSocketMessage(response);
        } catch (error) {
            console.error('Error processing audio WebSocket message:', error);
        }
    };
    
    audioWs.onerror = (error) => {
        console.error('Audio WebSocket error:', error);
        updateStatus('Error connecting to server');
        updateOrbState(null);
    };
    
    audioWs.onclose = () => {
        console.log('Audio WebSocket connection closed');
        updateStatus('Disconnected from server');
        updateOrbState(null);
    };
}

// Update initialization
window.addEventListener('load', () => {
    connectWebSockets();  // Only connect audio WebSocket initially
    initializeChat();
});

// Update cleanup
window.addEventListener('unload', () => {
    stopRecording();
    if (audioWs) {
        audioWs.close();
    }
    if (textWs) {
        textWs.close();
    }
});

async function startRecording() {
    if (!audioWs || audioWs.readyState !== WebSocket.OPEN) {
        connectWebSockets();
    }

    try {
        // Clear previous responses and errors
        console.log('Clearing previous responses');
        document.getElementById('error-message').classList.remove('visible');
        
        // Clear previous audio buffer
        audioBuffer = [];
        
        // Request microphone permissions explicitly
        const stream = await navigator.mediaDevices.getUserMedia({
            audio: {
                channelCount: 1,
                sampleRate: 44100,
                sampleSize: 16,
                echoCancellation: true,
                noiseSuppression: true
            }
        }).catch(error => {
            console.error('Microphone permission error:', error);
            if (error.name === 'NotAllowedError') {
                showError('Microphone access was denied. Please allow microphone access and try again.');
            } else if (error.name === 'NotFoundError') {
                showError('No microphone found. Please connect a microphone and try again.');
            } else {
                showError(`Error accessing microphone: ${error.message}`);
            }
            throw error;
        });

        // Create audio context
        audioContext = new AudioContext({
            sampleRate: 44100
        });

        isRecording = true;
        updateStatus('Recording...');
        updateOrbState('recording');

        // Process audio data
        const source = audioContext.createMediaStreamSource(stream);
        const processor = audioContext.createScriptProcessor(4096, 1, 1);

        source.connect(processor);
        processor.connect(audioContext.destination);

        processor.onaudioprocess = (e) => {
            if (!isRecording) return;
            
            // Convert audio data to 16-bit PCM
            const inputData = e.inputBuffer.getChannelData(0);
            const pcmData = new Int16Array(inputData.length);
            
            for (let i = 0; i < inputData.length; i++) {
                pcmData[i] = Math.max(-32768, Math.min(32767, Math.round(inputData[i] * 32768)));
            }
            
            // Store the PCM data in buffer
            audioBuffer.push(pcmData.buffer);
        };

        // Store the stream for cleanup
        audioStream = stream;

    } catch (error) {
        console.error('Error in startRecording:', error);
        updateStatus('Error accessing microphone');
        updateOrbState(null);
        // Error message is already shown by the catch block above
    }
}

async function stopRecording() {
    if (isRecording) {
        isRecording = false;
        updateStatus('Processing audio...');
        updateOrbState('processing');
        
        // Stop audio capture
        if (audioStream) {
            audioStream.getTracks().forEach(track => track.stop());
        }
        
        if (audioContext) {
            audioContext.close();
        }

        // Combine all audio chunks into a single buffer
        if (audioBuffer.length > 0 && audioWs && audioWs.readyState === WebSocket.OPEN) {
            // Calculate total length
            const totalLength = audioBuffer.reduce((acc, buffer) => acc + buffer.byteLength, 0);
            const combinedBuffer = new Int16Array(totalLength / 2);
            
            // Copy all chunks into the combined buffer
            let offset = 0;
            for (const buffer of audioBuffer) {
                const chunk = new Int16Array(buffer);
                combinedBuffer.set(chunk, offset);
                offset += chunk.length;
            }
            
            // Send the complete audio data
            console.log(`Sending complete audio data: ${combinedBuffer.byteLength} bytes`);
            audioWs.send(combinedBuffer.buffer);
        }
        
        // Clear the buffer
        audioBuffer = [];
    }
}

function toggleRecording() {
    if (isRecording) {
        stopRecording();
    } else {
        startRecording();
    }
}

async function deleteChat(chatId) {
    try {
        const response = await fetch(`http://localhost:8000/api/delete-chat/${chatId}`, {
            method: 'DELETE'
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Failed to delete chat');
        }

        // Remove chat from list
        const chatItem = document.querySelector(`.chat-item[data-chat-id="${chatId}"]`);
        if (chatItem) {
            chatItem.remove();
        }

        // If deleted chat was current chat, create a new one
        if (chatId === currentChatId) {
            await createNewChat();
        }

        showError('Chat deleted successfully');
    } catch (error) {
        console.error('Error deleting chat:', error);
        showError(error.message || 'Failed to delete chat');
    }
}

function handleCommandResponse(commandData) {
    if (!commandData) {
        console.error("No command data received");
        return;
    }

    // Handle general questions
    if (commandData.command_type === "general_question") {
        // Add the response to the chat
        addMessageToChat("assistant", commandData.response);
        
        // If follow-up is required, show the follow-up question
        if (commandData.requires_followup && commandData.followup_context) {
            setTimeout(() => {
                addMessageToChat("assistant", commandData.followup_context.question);
            }, 1000);
        }
        return;
    }

    // Handle other command types
    switch (commandData.command_type) {
        case "search_store":
            // ... existing search_store handling ...
            break;
        case "calendar_check":
            // ... existing calendar_check handling ...
            break;
        case "calendar_add":
            // ... existing calendar_add handling ...
            break;
        case "open_app":
            // ... existing open_app handling ...
            break;
        case "search_file":
            // ... existing search_file handling ...
            break;
        default:
            console.error("Unknown command type:", commandData.command_type);
    }
}

// Function to hide email dialog
function hideEmailDialog() {
    console.log('Hiding email dialog');
    emailDialog.classList.remove('visible');
    dialogOverlay.classList.remove('visible');
    currentCommandContext = null;  // Clear the command context
}

// Update email dialog event listeners
emailCancelButton.addEventListener('click', () => {
    console.log('Email cancelled by user');
    if (textWs && textWs.readyState === WebSocket.OPEN) {
        const message = {
            type: 'followup_response',
            response: '',
            cancelled: true,
            context: currentCommandContext
        };
        console.log('Sending cancel message:', message);
        textWs.send(JSON.stringify(message));
    } else {
        console.error('Text WebSocket not connected for cancel');
        showError('Connection error. Please try again.');
    }
    hideEmailDialog();
});

emailSendButton.addEventListener('click', () => {
    const emailAddress = emailInput.value.trim();
    console.log('Sending email to:', emailAddress);
    
    if (!emailAddress) {
        showError('Please enter an email address');
        return;
    }
    
    if (!emailAddress.includes('@')) {
        showError('Please enter a valid email address');
        return;
    }
    
    if (textWs && textWs.readyState === WebSocket.OPEN) {
        const message = {
            type: 'followup_response',
            response: emailAddress,
            cancelled: false,
            context: currentCommandContext
        };
        console.log('Sending email message:', message);
        textWs.send(JSON.stringify(message));
        // Hide dialog immediately after sending
        hideEmailDialog();
    } else {
        console.error('Text WebSocket not connected for email');
        showError('Connection error. Please try again.');
    }
});
