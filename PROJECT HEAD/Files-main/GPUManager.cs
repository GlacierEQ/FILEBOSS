// GPU Resource Management Class
using System;
using System.Management;
using System.Diagnostics;

public class GPUManager
{
    public static void EnablePersistentMode()
    {
        try
        {
            // Enable NVIDIA persistence mode for reliability
            var process = new Process
            {
                StartInfo = new ProcessStartInfo
                {
                    FileName = "nvidia-smi",
                    Arguments = "-pm 1",
                    UseShellExecute = false,
                    CreateNoWindow = true
                }
            };
            process.Start();
            process.WaitForExit();
        }
        catch (Exception ex)
        {
            Console.WriteLine($"Failed to enable persistence mode: {ex.Message}");
        }
    }
}
