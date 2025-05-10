let mediaRecorder;
let audioChunks = [];
let ws;
let isRecording = false;
let audioContext;
let audioStream;
let audioBuffer = [];

// UI Elements
const orb = document.getElementById('orb');
const statusText = document.getElementById('status');
const transcriptContainer = document.getElementById('transcript-container');
const commandContainer = document.getElementById('command-container');

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
    if (transcript) {
        transcriptElement.textContent = transcript;
        transcriptContainer.classList.add('visible');
        console.log('Transcription container made visible');
    } else {
        transcriptElement.textContent = 'No transcription available';
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

async function connectWebSocket() {
    ws = new WebSocket('ws://localhost:8000/ws/audio');
    
    ws.onopen = () => {
        console.log('WebSocket connection established');
        updateStatus('Ready to record');
    };
    
    ws.onmessage = (event) => {
        console.log('Received WebSocket message:', event.data);
        try {
            const response = JSON.parse(event.data);
            console.log('Parsed response:', response);
            
            switch(response.type) {
                case 'transcription':
                    console.log('Processing transcription response:', response);
                    if (response.error) {
                        console.log('Transcription error:', response.error);
                        updateStatus(`Error: ${response.error}`);
                        updateOrbState(null);
                        showTranscription('');
                    } else {
                        console.log('Showing transcription:', response.transcription);
                        updateStatus('Processing command...');
                        updateOrbState('processing');
                        showTranscription(response.transcription);
                    }
                    break;
                    
                case 'jarvis':
                    console.log('Processing JARVIS response:', response);
                    if (response.error) {
                        console.log('JARVIS error:', response.error);
                        updateStatus(`Error: ${response.error}`);
                        updateOrbState(null);
                        showJarvisResponse(response.error);
                    } else {
                        console.log('Showing JARVIS response:', response);
                        // Pass the entire response object to showJarvisResponse
                        showJarvisResponse(response);
                    }
                    break;
                    
                case 'error':
                    console.log('Processing error response:', response);
                    updateStatus(`Error: ${response.error}`);
                    updateOrbState(null);
                    showTranscription('');
                    showJarvisResponse(response.error);
                    break;
                    
                default:
                    console.log('Unknown response type:', response.type);
            }
        } catch (error) {
            console.error('Error processing WebSocket message:', error);
            console.error('Raw message:', event.data);
        }
    };
    
    ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        updateStatus('Error connecting to server');
        updateOrbState(null);
    };
    
    ws.onclose = () => {
        console.log('WebSocket connection closed');
        updateStatus('Disconnected from server');
        updateOrbState(null);
    };
}

async function startRecording() {
    if (!ws || ws.readyState !== WebSocket.OPEN) {
        connectWebSocket();
    }

    try {
        // Clear previous responses and errors
        console.log('Clearing previous responses');
        transcriptContainer.classList.remove('visible');
        commandContainer.classList.remove('visible');
        document.getElementById('transcript').textContent = 'Processing...';
        document.getElementById('command-response').textContent = 'Waiting for response...';
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
        showTranscription('');
        showJarvisResponse('');
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
        if (audioBuffer.length > 0 && ws && ws.readyState === WebSocket.OPEN) {
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
            ws.send(combinedBuffer.buffer);
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

// Connect WebSocket when the page loads
window.addEventListener('load', connectWebSocket);

// Clean up WebSocket connection when the page unloads
window.addEventListener('unload', () => {
    stopRecording();
    if (ws) {
        ws.close();
    }
});
