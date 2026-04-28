#Law Variant from other mods
set parent_laws 'law_national_supremacy' 'law_culutural_exclusion' 'law_racial_segregation' 'law_elected_bureaucrats' 'law_debt_slavery'


function probe_variants 
    for file in *.txt
        set parents (string match -rg 'parent = (law_[a-zA-Z_]*)' < $file )
        for parent in $parents
            if not contains $parent $parent_laws
                set -a parent_laws $parent
            end
        end
    end
end

cd ~/.local/share/Steam/steamapps/common/Victoria\ 3/game/common/laws
probe_variants
cd -
cd ../better-politics-mod/common/laws/
probe_variants
cd ../../

for parent in $parent_laws
    echo $parent
end

for lawtype in $parent_laws
    grep -rl "has_law = law_type:$lawtype"  .| xargs sed -i "s/has_law = law_type:$lawtype/has_law_or_variant = law_type:$lawtype/g"
end
