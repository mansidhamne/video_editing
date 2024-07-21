import time
import json
import wave
import moviepy.editor as mp
import whisper_timestamped as whisper
import Word as customWord
from vosk import Model, KaldiRecognizer, SetLogLevel

def recognize_audio_whisper(audio_path, model):
    audioclip = whisper.load_audio(audio_path)
    model = whisper.load_model(model, device = "cpu")
    
    print("Starting audio to text conversion!\n")
    start_time = time.time()
    
    result = whisper.transcribe(model, audioclip, language="en", plot_word_alignment=False)
    #print(json.dumps(result, indent = 2, ensure_ascii = False))

    words_list = []
    for segment in result["segments"]:
        for word in segment["words"]:
            word_dict = customWord.Word(word, model="whisper")
            words_list.append(word_dict)

    print("\nAudio to text conversion completed in {:.2f} seconds!\n".format(time.time() - start_time))

    text = ""
    for obj in words_list:
        text += obj.word + " "
    print("Text: ", text)

    return words_list

def recognize_audio_vosk(audio_path, model):
    wf = wave.open(audio_path, "rb")
    if wf.getnchannels() != 1 or wf.getsampwidth() != 2 or wf.getcomptype() != "NONE":
        print("Audio file must be WAV format mono PCM.")
        exit(1)

    start_time = time.time()
    rec = KaldiRecognizer(model, wf.getframerate())
    rec.SetWords(True)

    results = []
    while True:
        data = wf.readframes(4000)
        if len(data) == 0:
            break
        if rec.AcceptWaveform(data):
            res = json.loads(rec.Result())
            results.append(res)
    
    res = json.loads(rec.FinalResult())
    results.append(res)

    words_list = []
    for sentence in results:
        if len(sentence) == 1:
            continue
        for obj in sentence['result']:
            w = customWord.Word(obj, model="vosk")  
            words_list.append(w)  

    text = ''
    for w in words_list:
        text += w.word + ' '

    time_elapsed = time.strftime('%H:%M:%S',
                                 time.gmtime(time.time() - start_time))
    print(f'Done! Elapsed time = {time_elapsed}')

    print("\n\tVosk thinks you said:\n")
    print(text)

    wf.close 

    return words_list

def segments_from_silence(words_list, threshold=2, offset=0.3):

    starts = []
    ends = []

    for i in range(len(words_list) - 1):
        cw = words_list[i]
        nw = words_list[i + 1]
        if nw.start - cw.end > threshold:
            starts.append(cw.end + offset)
            ends.append(nw.start - offset)
        
    print("Starts: ", starts)
    print("Ends: ", ends)   

    segments = []
    length = max(len(starts), len(ends))
    for i in range(length + 1):
        if i == 0:
            segments.append((0, starts[0]))
        elif i == length:
            segments.append((ends[i-1], None))
        else:
            segments.append((ends[i-1], starts[i]))

    print("The search of silence is completed. Got the following array of segments: \n")
    print(segments)

    return segments

def crop_video(video, segments, result_path, bitrate=None):
    clips = []

    for start, end in segments:
        clips.append(video.subclip(start, end))

    new_clip = mp.concatenate_videoclips(clips)
    new_video = new_clip.set_audio(new_clip.audio)
    new_video.write_videofile(result_path, audio_codec='aac')

def main(model, video_path, result_path, threshold=2, offset_silence=0.3, bitrate=None):
    #vosk model
    # print(f"Reading your vosk model '{model_path_vosk}'...")
    # model = Model(model_path_vosk)
    # print(f"'{model_path_vosk}' model was successfully read")

    # audio_path = video_path[:-3] + "wav"
    # clip = mp.VideoFileClip(video_path)
    # clip.audio.write_audiofile(audio_path, ffmpeg_params=["-ac", "1"])
    # words_list = recognize_audio_vosk(audio_path=audio_path,model=model)
    # segments_vosk = segments_from_silence(words_list, threshold=threshold, offset=offset_silence)
    # crop_video(video=clip, segments=segments_vosk, result_path=result_path_vosk, bitrate=bitrate)
    
    #whisper model
    clip = mp.VideoFileClip(video_path)
    audio = clip.audio
    audio.write_audiofile("audio-2-whisper.mp3")
    audio_path = "audio-2-whisper.mp3"
    words_list = recognize_audio_whisper(audio_path=audio_path, model=model)
    segments_whisper = segments_from_silence(words_list, threshold=threshold, offset=offset_silence)
    crop_video(video=clip, segments=segments_whisper, result_path=result_path_whisper, bitrate=bitrate)
    

if __name__ == '__main__':

    video_path = "sample-2.mp4"
    result_path_vosk = "sample-2-vosk.mp4"
    result_path_whisper = "sample-2-whisper.mp4"

    model_path_whisper = "base"

    model_path_vosk = "vosk-model-en-us-0.22"

    bitrate = None 
    threshold = 2
    offset_silence = 0.3

    #vosk model
    # main(model=model_path_vosk, video_path=video_path, result_path=result_path_vosk,
    #      threshold=threshold, offset_silence=offset_silence, 
    #      bitrate=bitrate)

    #whisper model
    main(model=model_path_whisper, video_path=video_path, result_path=result_path_whisper,
         threshold=threshold, offset_silence=offset_silence, 
         bitrate=bitrate)