using UnityEngine;
using UnityEngine.SceneManagement;

// This script is used to handle the main menu UI via the functions exposed to the UI buttons

public class MainMenu : MonoBehaviour
{
    [SerializeField] private AudioClip buttonClickSound;

    [SerializeField] private AudioClip bgm;

    private void Start()
    {
        if (AudioManager.Instance != null)
        {
            AudioManager.Instance.SetBGMVolume(0.1f);
            AudioManager.Instance.PlayBGM(bgm);
        }
    }

    public void PlayGame() //Assume the first scene is the main menu, then the next scene is the game
    {
        if (AudioManager.Instance != null)
            AudioManager.Instance.PlaySound(buttonClickSound);
        SceneManager.LoadScene(SceneManager.GetActiveScene().buildIndex + 1);
    }

    public void QuitGame()
    {
        if (AudioManager.Instance != null)
            AudioManager.Instance.PlaySound(buttonClickSound);
        #if UNITY_EDITOR
        UnityEditor.EditorApplication.isPlaying = false;
        #else
        Application.Quit();
        #endif
    }
}
