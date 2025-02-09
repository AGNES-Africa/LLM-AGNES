import React from "react";
import { Mic } from 'lucide-react';

interface IProps {
  onFinish: ({ id, audio }: { id: string; audio: Blob }) => void;
}

const AudioRecorder: React.FC<IProps> = ({ onFinish }) => {
  const [isRecording, setIsRecording] = React.useState<boolean>(false);

  const [stream, setStream] = React.useState<MediaStream | null>(null);
  const [voiceRecorder, setVoiceRecorder] =
    React.useState<MediaRecorder | null>(null);

  const [content, setContent] = React.useState<Blob | null>(null);

  const onAudioClick = async () => {
    try {
      const audioStream = await navigator.mediaDevices.getUserMedia({
        audio: true,
      });

      const mediaRecorder = new MediaRecorder(audioStream);

      setStream(audioStream);
      setVoiceRecorder(mediaRecorder);
      setIsRecording(true);
    } catch (e) {
      console.log("User didn't allowed us to access the microphone.");
    }
  };

  const onStopRecording = () => {
    if (!isRecording || !stream || !voiceRecorder) return;

    const tracks = stream.getAudioTracks();

    for (const track of tracks) {
      track.stop();
    }

    voiceRecorder.stop();

    setVoiceRecorder(null);
    setIsRecording(false);
  };

  /**
   * This hook is triggered when we start the recording
   */
  React.useEffect(() => {
    if (!isRecording || !voiceRecorder) return;

    voiceRecorder.start();

    voiceRecorder.ondataavailable = ({ data }) => setContent(data);
  }, [isRecording, voiceRecorder]);

  /**
   * This hook will call our callback after finishing the record
   */
  React.useEffect(() => {
    if (isRecording || !content || !stream) return;

    onFinish({ id: stream.id, audio: content });

    setStream(null);
    setContent(null);
  }, [isRecording, content]);

  return (
    <button
    onClick={(event) => {
        event.preventDefault(); // Prevent default form submission
        if (!isRecording) {
          onAudioClick();
        } else {
          onStopRecording();
       }
    }}
    className={`px-4 py-2 rounded-r-lg transition-colors duration-300 ${
        isRecording
          ? "bg-red-500 text-white animate-pulse hover:bg-red-500"
          : "bg-white text-blue-500 px-4 py-2 rounded-r-lg hover:bg-blue-600"
      }`}
    >
       <Mic />
    </button>
  );
};

export default AudioRecorder;