# Reference
```
some_class = {
    social_hierarchy = some_hierarchy
    strata = lower / middle / upper

    allowed_professions = {
        <list of professions>
    }

    pop_criteria = {
        <trigger conditions>
    }
}
```

# Requirements
At least one valid social class per strata must be scripted for each hierarhcy
in order for the game to function.

I.e. at least 3 social classes needs to exist referencing the `some_hierarchy`
social hierarchy, one or more with `strata = lower`, one or more with
`strata = middle`, and one or more with `strata = upper`.

A pop should unambiguously fall into one of the social classes scripted for
the relevant hierarchy. This is determined in accordance with both
`allowed_professions` and `pop_criteria`. If there is ambiguity, the class in
which a pop will fall is unspecified. It will likely be the first one
(in script order) for which the pop matches both `allowed_professions` and
`pop_criteria` for, but do not rely on this behavior.

Every pop subject to a social hierarchy must fall in one of the scripted
social classes pertaining to that hierarchy. If this is not true,
mayhem will ensue: anything from the game crashing, to the game running but
with a bunch of things bugging out, to savegame corruption, and anything
in between is possible.

Note: the requirement that each pop should fall in exactly one of the social
classes pertaining to a hierarchy does not mean that at least one pop needs to
fall into every class. For example, it's totally possible to script
3 social classes such that every pop falls into the same class (maybe to
simulate a "perfeclty egalitarian" stratification?). I am unsure about the
gameplay effects of this though, as it would mean that 2 of the 3 stratas would
be empty (at least for pops subject to the hierarchy, the other ones fall back
to the default hierarchy, see the social hierarchy documentation for more info).

Social classes work in combination with social hierarchies, check the
documentation for those too to have a better picture.

Note: if `pop_criteria` is missing, it's equivalent to `always = yes`. If
`allowed_professions` is missing, it's equivalent to the empty list i.e. no
profession is allowed to be part of that social class.

# Example
```
social_class_1 = {
    social_hierarchy = some_hierarchy
    strata = lower

    allowed_professions = {
        slaves
        peasants
    }

    pop_criteria = {
        religion = { NOT = { has_discrimination_trait = heritage_christian } }
    }
}

social_class_2 = {
    social_hierarchy = some_hierarchy
    strata = middle

    allowed_professions = {
        <every profession>
    }

    pop_criteria = {
        NOT = { has_pop_religion = catholic }
        religion = { has_discrimination_trait = heritage_christian }
    }
}

social_class_3 = {
    social_hierarchy = some_hierarchy
    strata = upper

    allowed_professions = {
        <every profession except clergymen>
    }

    pop_criteria = {
        has_pop_religion = catholic
    }
}

social_class_4 = {
    social_hierarchy = some_hierarchy
    strata = upper

    allowed_professions = {
        clergymen
    }

    pop_criteria = {
        has_pop_religion = catholic
    }
}
```

In this example, the 4 social classes pertain to the `some_hierarchy`
social hierarchy, with different pops falling into different classes depending
on the pop's profession and religion.
This example could simulate a sort of catholic supremacist social stratification
where catholic clergymen are at the top together with every other catholic pop,
with non-catholic christians following, and every non-christian pop tailing.

This example is an egalitarian stratification when it comes to profession, but
a decidedly non-egalitarian one when it comes to religion.

As shown, more than one class can be part of the same strata. In this example,
both `social_class_3` and `social_class_4` are considered to be in the upper
strata.

This is useful for both flavoring and narrative content, where events or other
scripted content might want to refer to certain social classes specifically.

# List of scriptable keys
## social_hierarchy
This stipulates which hierarchy the social class pertains to. This is the key
of a social hierarchy scripted in `game/common/social_hierarchies`.

## strata
You might or might not remember strata being scripted on a pop type. This is
no longer the case. Pop types no longer belong to a strata, social classes do.

Every pop belongs to a social class, and that class is considered to be part of
one of 3 possible stratas: lower, middle, or upper. Which pops belong to a
certain class is determined by the `pop_criteria` trigger.

## allowed_professions
This is an exhaustive list of professions that are allowed to be part of this
social class. If a profession is not present in the list, pops of that
profession will not be part of this social class.

Professions can overlap across different social classes. In the example above,
a clerk could fall into `social_class_1`, `social_class_2`, or `social_class_3`.

## pop_criteria
This is a trigger that, together with `allowed_professions`, determines whether
a pop belongs to a social class.
Every pop _must_ fall in exactly one of the social classes pertaining to the
social hierarchy they are subject to.

Using the example above, if we have determined that a pop is subject to
`some_hierarchy`, then this pop must unequivocally and unambiguously fall into
exactly one of `social_class_1`, `social_class_2`, `social_class_3`,
or `social_class_4`.

Note: because of the requirement that each pop must fall in one of the social
classes pertaining to a hierarchy, it might be tempting to script one social
class as a catch-all, with every profession in `allowed_professions` and
`pop_criteria = { always = yes }`. This is fine, but make sure that such a
social class is last in script order among those pertaining to the same
social hierarchy.
