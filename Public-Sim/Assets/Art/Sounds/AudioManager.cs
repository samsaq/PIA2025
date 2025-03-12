using UnityEngine;
using System.Collections;

public class AudioManager : MonoBehaviour
{
    // Simple singleton audio manager to play sounds even when the scene is changed
    private static AudioManager instance;
    public static AudioManager Instance { get { return instance; } }
    
    [Header("Audio Sources")]
    [SerializeField] private AudioSource sfxSource;
    [SerializeField] private AudioSource bgmSource;
    
    [Header("Settings")]
    [SerializeField] private float bgmFadeDuration = 1.0f;
    
    private AudioClip currentBgm;
    private float bgmVolume = 1.0f;
    private Coroutine fadeCoroutine;
    
    private void Awake()
    {
        if (instance == null)
        {
            instance = this;
            DontDestroyOnLoad(gameObject);
            
            // Setup SFX source
            if (sfxSource == null)
            {
                sfxSource = gameObject.AddComponent<AudioSource>();
            }
            
            // Setup BGM source
            if (bgmSource == null)
            {
                bgmSource = gameObject.AddComponent<AudioSource>();
                bgmSource.loop = true;
                bgmSource.playOnAwake = false;
            }
            
            bgmVolume = bgmSource.volume;
        }
        else
        {
            Destroy(gameObject);
        }
    }
    
    // SFX Methods
    public void PlaySound(AudioClip clip)
    {
        if (clip != null)
            sfxSource.PlayOneShot(clip);
    }
    
    public void PlaySoundWithVolume(AudioClip clip, float volume)
    {
        if (clip != null)
            sfxSource.PlayOneShot(clip, volume);
    }
    
    // BGM Methods
    public void PlayBGM(AudioClip music)
    {
        if (music == null) return;
        
        if (currentBgm == music && bgmSource.isPlaying) return;
        
        currentBgm = music;
        
        if (fadeCoroutine != null)
            StopCoroutine(fadeCoroutine);
            
        fadeCoroutine = StartCoroutine(FadeBGM(0, bgmVolume, bgmFadeDuration, true));
    }
    
    public void StopBGM()
    {
        if (fadeCoroutine != null)
            StopCoroutine(fadeCoroutine);
            
        fadeCoroutine = StartCoroutine(FadeBGM(bgmSource.volume, 0, bgmFadeDuration, false));
    }
    
    public void PauseBGM()
    {
        bgmSource.Pause();
    }
    
    public void ResumeBGM()
    {
        bgmSource.UnPause();
    }
    
    public void SetBGMVolume(float volume)
    {
        bgmVolume = Mathf.Clamp01(volume);
        bgmSource.volume = bgmVolume;
    }
    
    public float GetBGMVolume()
    {
        return bgmVolume;
    }
    
    public bool IsBGMPlaying()
    {
        return bgmSource.isPlaying;
    }
    
    public void RestartBGM()
    {
        if (currentBgm != null)
        {
            bgmSource.Stop();
            bgmSource.clip = currentBgm;
            bgmSource.Play();
        }
    }
    
    public void CrossfadeBGM(AudioClip newMusic, float fadeDuration = 1.0f)
    {
        if (newMusic == null) return;
        if (currentBgm == newMusic && bgmSource.isPlaying) return;
        
        if (fadeCoroutine != null)
            StopCoroutine(fadeCoroutine);
            
        fadeCoroutine = StartCoroutine(CrossfadeRoutine(newMusic, fadeDuration));
    }
    
    private IEnumerator FadeBGM(float startVolume, float targetVolume, float duration, bool playNew)
    {
        float timer = 0;
        
        if (playNew)
        {
            bgmSource.clip = currentBgm;
            bgmSource.volume = startVolume;
            bgmSource.Play();
        }
        
        while (timer < duration)
        {
            timer += Time.deltaTime;
            bgmSource.volume = Mathf.Lerp(startVolume, targetVolume, timer / duration);
            yield return null;
        }
        
        bgmSource.volume = targetVolume;
        
        if (targetVolume <= 0)
            bgmSource.Stop();
            
        fadeCoroutine = null;
    }
    
    private IEnumerator CrossfadeRoutine(AudioClip newMusic, float duration)
    {
        // Create a temporary audio source for the new track
        AudioSource tempSource = gameObject.AddComponent<AudioSource>();
        tempSource.clip = newMusic;
        tempSource.loop = true;
        tempSource.volume = 0;
        tempSource.Play();
        
        float timer = 0;
        float startVolume = bgmSource.volume;
        
        while (timer < duration)
        {
            timer += Time.deltaTime;
            float t = timer / duration;
            bgmSource.volume = Mathf.Lerp(startVolume, 0, t);
            tempSource.volume = Mathf.Lerp(0, bgmVolume, t);
            yield return null;
        }
        
        // Stop and clean up the old music
        bgmSource.Stop();
        bgmSource.clip = newMusic;
        bgmSource.volume = bgmVolume;
        bgmSource.Play();
        
        // Remove the temporary source
        Destroy(tempSource);
        currentBgm = newMusic;
        fadeCoroutine = null;
    }
}