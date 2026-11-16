#!/usr/bin/env nu

# Adds `dlc = dlc_bpm` to every top-level journal entry that isn't a vanilla
# override (i.e. any entry whose key has a `PREFIX:` like `REPLACE:` is skipped).
# Idempotent: entries that already have a `dlc = ...` line are left alone.

const BOM = "\u{FEFF}"

# net brace change on a line, ignoring comments and quoted strings
def brace-delta [line: string]: nothing -> int {
    let code = ($line | str replace --all --regex '"(?:[^"\\]|\\.)*"' '""' | str replace --regex '#.*$' '')
    let opens = ($code | split chars | where $it == "{" | length)
    let closes = ($code | split chars | where $it == "}" | length)
    $opens - $closes
}

def process-file [file: path, dry_run: bool]: nothing -> int {
    let raw = (open --raw $file | decode utf-8)
    let has_bom = ((open --raw $file | into binary | bytes at 0..2) == 0x[EF BB BF])
    let text = ($raw | str replace --regex "^\u{FEFF}" "")
    let trailing_nl = ($text | str ends-with "\n")
    let src = ($text | lines)

    # pass 1: find entry start lines (depth 0 -> `key = {` with no prefix)
    # and whether each already has a depth-1 `dlc =` line
    mut depth = 0
    mut current = ""
    mut starts = {}  # line index (as string) -> has_dlc
    for row in ($src | enumerate) {
        let line = $row.item
        if $depth == 0 {
            let m = ($line | parse --regex '^\s*(?P<key>[\w.:]+)\s*=\s*\{')
            if ($m | is-not-empty) and not ($m.0.key | str contains ":") {
                $current = ($row.index | into string)
                $starts = ($starts | upsert $current false)
            } else {
                $current = ""
            }
        } else if $depth == 1 and $current != "" and ($line =~ '^\s*dlc\s*=') {
            $starts = ($starts | upsert $current true)
        }
        $depth = $depth + (brace-delta $line)
    }

    let targets = ($starts | transpose idx has_dlc | where not has_dlc | get idx | each { into int })
    if ($targets | is-empty) { return 0 }

    for idx in $targets {
        print $"  + ($src | get $idx | str trim)"
    }
    if $dry_run { return ($targets | length) }

    # pass 2: rebuild with the dlc line inserted after each target opener
    let out = ($src | enumerate | each {|row|
        if $row.index in $targets {
            [$row.item "\tdlc = dlc_bpm" ""]
        } else {
            [$row.item]
        }
    } | flatten | str join "\n")

    let out = if $trailing_nl { $out + "\n" } else { $out }
    let out = if $has_bom { $BOM + $out } else { $out }
    $out | save --raw --force $file
    $targets | length
}

def main [
    dir: path = "../better-politics-mod/common/journal_entries"
    --dry-run (-n)  # only print what would change
] {
    mut total = 0
    for file in (glob $"($dir)/**/*.txt" | sort) {
        print $"($file | path basename)"
        $total = $total + (process-file $file $dry_run)
    }
    let verb = if $dry_run { "would add" } else { "added" }
    print $"\n($verb) dlc to ($total) journal entries"
}
