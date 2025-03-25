import torch
import numpy as np
from sklearn.cluster import AgglomerativeClustering
from sklearn.metrics import silhouette_score

def load_silero_vad():
    """
    Load the Silero VAD model and helper functions.
    """
    try:
        print("Loading Silero VAD model...")
        model, utils = torch.hub.load(repo_or_dir='snakers4/silero-vad',
                                      model='silero_vad',
                                      force_reload=True,
                                      onnx=False)
        (get_speech_timestamps, _, read_audio, _, _) = utils
        return model, get_speech_timestamps, read_audio
    except Exception as e:
        print(f"Error loading Silero VAD: {e}")
        return None, None, None

def get_speech_embeddings(audio_path, vad_model, get_speech_timestamps, read_audio):
    """
    Detect speech segments and compute simple embeddings.
    Returns an array of embeddings and a list of segment dictionaries.
    """
    try:
        wav = read_audio(audio_path, sampling_rate=16000)
        speech_timestamps = get_speech_timestamps(wav, vad_model, sampling_rate=16000, 
                                                    min_speech_duration_ms=500, 
                                                    max_speech_duration_s=float('inf'),
                                                    min_silence_duration_ms=500)
        print(f"Detected {len(speech_timestamps)} speech segments")
        embeddings = []
        segments = []
        
        def get_speech_segment(start_sample, end_sample):
            return wav[start_sample:end_sample]
        
        for i, segment in enumerate(speech_timestamps):
            start_sample = segment['start']
            end_sample = segment['end']
            speech_segment = get_speech_segment(start_sample, end_sample)
            if len(speech_segment) < 1600:
                continue
            # Use clone().detach() to avoid warnings.
            segment_tensor = torch.tensor(speech_segment).clone().detach().float()
            spec = torch.stft(
                segment_tensor,
                n_fft=512,
                hop_length=160,
                win_length=400,
                window=torch.hann_window(400),
                return_complex=True
            )
            spec = torch.abs(spec)
            freq_bands = [(0, 10), (10, 20), (20, 50), (50, 100), (100, 256)]
            feature_vector = []
            for low, high in freq_bands:
                band_energy = torch.mean(spec[low:high, :]).item()
                feature_vector.append(band_energy)
            zero_crossings = torch.sum(torch.abs(torch.sign(segment_tensor[1:]) - torch.sign(segment_tensor[:-1]))).item() / 2
            zero_crossing_rate = zero_crossings / len(segment_tensor)
            feature_vector.append(zero_crossing_rate)
            energy = torch.mean(torch.abs(segment_tensor)).item()
            feature_vector.append(energy)
            start_time = start_sample / 16000
            end_time = end_sample / 16000
            embeddings.append(feature_vector)
            segments.append({
                'start': start_time,
                'end': end_time,
                'length': end_time - start_time
            })
        return np.array(embeddings), segments
    except Exception as e:
        print(f"Error extracting speech embeddings: {e}")
        return None, None

def cluster_speakers(embeddings, segments, min_speakers=2, max_speakers=5):
    """
    Cluster speech segments to assign speaker labels.
    """
    if len(embeddings) == 0:
        print("No speech segments detected")
        return []
    
    embeddings = (embeddings - np.mean(embeddings, axis=0)) / (np.std(embeddings, axis=0) + 1e-8)
    best_score = -1
    best_labels = None
    best_n_clusters = min_speakers
    max_speakers = min(max_speakers, len(embeddings))
    
    for n_clusters in range(min_speakers, max_speakers + 1):
        if n_clusters >= len(embeddings):
            continue
        
        # Remove affinity parameter when using ward linkage.
        clustering = AgglomerativeClustering(n_clusters=n_clusters, linkage='ward')
        labels = clustering.fit_predict(embeddings)
        if n_clusters == 1 or len(set(labels)) <= 1:
            continue
        score = silhouette_score(embeddings, labels)
        print(f"Clusters: {n_clusters}, Silhouette Score: {score:.3f}")
        if score > best_score:
            best_score = score
            best_labels = labels
            best_n_clusters = n_clusters
    
    for i, segment in enumerate(segments):
        if i < len(best_labels):
            segment['speaker'] = f"Speaker {best_labels[i] + 1}"
    print(f"Selected {best_n_clusters} speakers with silhouette score: {best_score:.3f}")
    return segments

def assign_transcript_to_speakers(whisper_segments, vad_segments):
    """
    Align transcript segments from Whisper with VAD segments based on time overlap.
    """
    for w_segment in whisper_segments:
        w_start = w_segment['start']
        w_end = w_segment['end']
        best_overlap = 0
        best_speaker = "Unknown"
        for v_segment in vad_segments:
            v_start = v_segment['start']
            v_end = v_segment['end']
            overlap_start = max(w_start, v_start)
            overlap_end = min(w_end, v_end)
            if overlap_end > overlap_start:
                overlap_duration = overlap_end - overlap_start
                if overlap_duration > best_overlap:
                    best_overlap = overlap_duration
                    if 'speaker' in v_segment:
                        best_speaker = v_segment['speaker']
        w_segment['speaker'] = best_speaker
    return whisper_segments
