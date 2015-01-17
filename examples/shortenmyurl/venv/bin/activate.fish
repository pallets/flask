# This file must be used with "source bin/activate.fish" *from fish* (http://fishshell.com)
# you cannot run it directly

function deactivate  -d "Exit virtualenv and return to normal shell environment"
    # reset old environment variables
    if test -n "$_OLD_VIRTUAL_PATH" 
        set -gx PATH $_OLD_VIRTUAL_PATH
        set -e _OLD_VIRTUAL_PATH
    end
    if test -n "$_OLD_VIRTUAL_PYTHONHOME"
        set -gx PYTHONHOME $_OLD_VIRTUAL_PYTHONHOME
        set -e _OLD_VIRTUAL_PYTHONHOME
    end
    
    if test -n "$_OLD_FISH_PROMPT_OVERRIDE"
        # set an empty local fish_function_path, so fish_prompt doesn't automatically reload
        set -l fish_function_path
        # erase the virtualenv's fish_prompt function, and restore the original
        functions -e fish_prompt
        functions -c _old_fish_prompt fish_prompt
        functions -e _old_fish_prompt
        set -e _OLD_FISH_PROMPT_OVERRIDE
    end
    
    set -e VIRTUAL_ENV
    if test "$argv[1]" != "nondestructive"
        # Self destruct!
        functions -e deactivate
    end
end

# unset irrelevant variables
deactivate nondestructive

set -gx VIRTUAL_ENV "/home/melvin/development/shortenmyurl/venv"

set -gx _OLD_VIRTUAL_PATH $PATH
set -gx PATH "$VIRTUAL_ENV/bin" $PATH

# unset PYTHONHOME if set
if set -q PYTHONHOME
    set -gx _OLD_VIRTUAL_PYTHONHOME $PYTHONHOME
    set -e PYTHONHOME
end

if test -z "$VIRTUAL_ENV_DISABLE_PROMPT"
    # fish uses a function instead of an env var to generate the prompt.
    
    # copy the current fish_prompt function as the function _old_fish_prompt
    functions -c fish_prompt _old_fish_prompt
    
    # with the original prompt function copied, we can override with our own.
    function fish_prompt
        # Prompt override?
        if test -n ""
            printf "%s%s" "" (set_color normal)
            _old_fish_prompt
            return
        end
        # ...Otherwise, prepend env
        set -l _checkbase (basename "$VIRTUAL_ENV")
        if test $_checkbase = "__"
            # special case for Aspen magic directories
            # see http://www.zetadev.com/software/aspen/
            printf "%s[%s]%s " (set_color -b blue white) (basename (dirname "$VIRTUAL_ENV")) (set_color normal) 
            _old_fish_prompt
        else
            printf "%s(%s)%s" (set_color -b blue white) (basename "$VIRTUAL_ENV") (set_color normal)
            _old_fish_prompt
        end
    end 
    
    set -gx _OLD_FISH_PROMPT_OVERRIDE "$VIRTUAL_ENV"
end
