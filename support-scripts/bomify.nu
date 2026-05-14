#!/usr/bin/env nu

def has-bom [file: path]: nothing -> bool {
    let header = (open --raw $file | bytes at 0..2)
    $header == 0x[EF BB BF]
}

def prepend-bom [file: path] {
    let contents: binary = (open --raw $file | into binary)
    let bom = 0x[EF BB BF]
    $bom ++ $contents | save --raw --force $file
}

def main [dir: path = "../better-politics-mod"] {
    let txt_files = (
        glob $"($dir)/**/*.txt"
    )

    if ($txt_files | is-empty) {
        print "No .txt files found."
        return
    }

    for file in $txt_files {
        if (has-bom $file) {
            print $"[skipped]  ($file)"
        } else {
            prepend-bom $file
            print $"[added] ($file)"
        }
    }
}
