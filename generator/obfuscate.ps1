param (
	[String]$Filename, 
	[String]$Command
)


$Content = [IO.File]::ReadAllLines($Filename)
$Script = [Scriptblock]::Create($Content)
Import-Module ./Invoke-Obfuscation/Invoke-Obfuscation.psd1; Invoke-Obfuscation -ScriptBlock $Script -Command $Command -Quiet