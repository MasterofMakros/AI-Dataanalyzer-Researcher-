# Start filling gaps
$baseDir = "F:\AI-Dataanalyzer-Researcher\tests\ground_truth"

$allFormats = @("pdf", "docx", "xlsx", "pptx", "doc", "xls", "ppt", "odt", "ods", "odp", "rtf", "txt", "html", "xml", "json", "csv", "md", "py", "js", "ts", "tsx", "jsx", "sh", "ps1", "sql", "css", "lua", "c", "cpp", "cc", "cxx", "h", "hpp", "java", "go", "rs", "rb", "php", "swift", "kt", "scala", "r", "pl", "pm", "asm", "bas", "vb", "cs", "fs", "hs", "elm", "clj", "ex", "exs", "erl", "dart", "vue", "svelte", "scss", "sass", "less", "styl", "coffee", "bat", "cmd", "awk", "sed", "makefile", "cmake", "gradle", "groovy", "yaml", "yml", "ini", "toml", "conf", "srt", "vtt", "sub", "epub", "mobi", "azw", "azw3", "jpg", "jpeg", "png", "gif", "bmp", "tiff", "tif", "webp", "heic", "psd", "raw", "cr2", "nef", "dng", "arw", "svg", "ico", "cur", "pcx", "tga", "exr", "hdr", "mp3", "wav", "flac", "m4a", "aac", "ogg", "wma", "mid", "midi", "ape", "opus", "amr", "au", "aiff", "aif", "mp4", "mkv", "avi", "mov", "wmv", "webm", "flv", "mpg", "mpeg", "m4v", "3gp", "rm", "rmvb", "vob", "mts", "m2ts", "ts", "eml", "msg", "zip", "rar", "7z", "tar", "gz", "bz2", "xz", "lz", "lzma", "cab", "iso", "dmg", "woff", "woff2", "ttf", "otf", "eot", "apk", "ipa", "xapk", "apkm", "exe", "dll", "sys", "elf", "bin", "rst", "tex", "cls", "bib", "log", "diff", "patch")

function Create-Dummy($Path, $HeaderHex) {
    $bytes = [byte[]]::new(1024)
    if ($HeaderHex) {
        $header = $HeaderHex -split ' ' | ForEach-Object { [Convert]::ToByte($_, 16) }
        [Array]::Copy($header, $bytes, $header.Length)
    } else {
        # Text dummy
        $text = "DUMMY CONTENT FOR TESTING"
        $enc = [System.Text.Encoding]::UTF8.GetBytes($text)
        [Array]::Copy($enc, $bytes, $enc.Length)
    }
    [System.IO.File]::WriteAllBytes($Path, $bytes)
}

# Magic Map
$magic = @{
    "exe" = "4D 5A"; "dll" = "4D 5A"; "sys" = "4D 5A"
    "elf" = "7F 45 4C 46"; "bin" = "00"
    "apk" = "50 4B 03 04"; "ipa" = "50 4B 03 04"; "xapk" = "50 4B 03 04"; "apkm" = "50 4B 03 04"
    "woff" = "77 4F 46 46"; "woff2" = "77 4F 46 32"; "ttf" = "00 01 00 00"; "otf" = "4F 54 54 4F"
    "pdf" = "25 50 44 46"; "jpg" = "FF D8 FF"; "png" = "89 50 4E 47"
    "zip" = "50 4B 03 04"; "rar" = "52 61 72 21"; "7z" = "37 7A BC AF"
    "mp3" = "49 44 33"; "wav" = "52 49 46 46"
}

Write-Host "Checking coverage and filling gaps..."

foreach ($ext in $allFormats) {
    $files = Get-ChildItem -Path $baseDir -Recurse -Filter "*.$ext"
    $count = $files.Count
    
    if ($count -lt 3) {
        $needed = 3 - $count
        Write-Host "  $ext : Found $count, creating $needed dummies"
        
        # Determine directory based on existing map concept
        $dir = "$baseDir\misc"
        if ("jpg,png,gif,bmp,tiff,webp,heic,svg,ico,psd,raw,cr2,nef,dng,arw,cur,pcx,tga,exr,hdr" -contains $ext) { $dir = "$baseDir\images" }
        elseif ("mp3,wav,flac,m4a,aac,ogg,wma,mid,midi,ape,opus,amr,au,aiff,aif" -contains $ext) { $dir = "$baseDir\audio" }
        elseif ("mp4,mkv,avi,mov,wmv,webm,flv,mpg,mpeg,m4v,3gp,rm,rmvb,vob,mts,m2ts,ts" -contains $ext) { $dir = "$baseDir\video" }
        elseif ("zip,rar,7z,tar,gz,bz2,xz,lz,lzma,cab,iso,dmg" -contains $ext) { $dir = "$baseDir\archive" }
        elseif ("exe,dll,sys,elf,bin" -contains $ext) { $dir = "$baseDir\binary" }
        elseif ("apk,ipa,xapk,apkm" -contains $ext) { $dir = "$baseDir\apps" }
        elseif ("woff,woff2,ttf,otf,eot" -contains $ext) { $dir = "$baseDir\fonts" }
        elseif ("epub,mobi,azw,azw3,djvu" -contains $ext) { $dir = "$baseDir\ebooks" }
        elseif ("py,js,ts,java,go,rs,cpp,c,h,sh" -contains $ext) { $dir = "$baseDir\code" }
        
        if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
        
        for ($i=1; $i -le $needed; $i++) {
            $name = "dummy_test_$i.$ext"
            if ($i -eq 1 -and $count -eq 0) { $name = "test.$ext" }
            $path = Join-Path $dir $name
            
            $header = $magic[$ext]
            Create-Dummy $path $header
        }
    }
}

Write-Host "Gap filling complete."
