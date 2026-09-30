# Shared helpers for the run scripts of the wicking cases.
# Source from a case folder:  . ../runTools.sh

# runTmpLog <logName> <command...>
#
# Runs the command with its log written in /tmp instead of the case folder.
# The solvers flush their log after every line; written inside the VSCode
# workspace this slows the run (hybridPorousInterFoam 1D: +20 %, impesFoam
# 1D: 73 s -> 115-209 s). Piping the output through a filter costs as much,
# so the log goes straight to a file outside the workspace.
#
# During the run <logName> in the case folder is a symlink to the real log
# (tail/grep work as usual). At the end the log is moved into the case
# folder. With LOG_EVERY=N (N > 1) in the environment only the header, the
# first 10 time steps and every Nth time step are kept, plus the last 400
# lines in <logName>.tail: use it for long runs (the log is ~0.4-0.9 kB per
# time step, i.e. GBs for millions of steps).
#
# If the script is killed, the symlink stays and the full log is still in
# /tmp/<case>.XXXXXX/ (a reboot may clear /tmp).
# Returns the exit status of the command.
runTmpLog()
{
    _log=$1
    shift

    _logDir=$(mktemp -d /tmp/$(basename "$PWD").XXXXXX)
    rm -f "$_log"
    ln -s "$_logDir/$_log" "$_log"

    "$@" > "$_logDir/$_log" 2>&1
    _status=$?

    rm -f "$_log"
    if [ "${LOG_EVERY:-1}" -gt 1 ]
    then
        awk -v N="$LOG_EVERY" '
            BEGIN { keep = 1 }
            /^Time = / { n++; keep = (n <= 10 || n % N == 0) }
            keep
        ' "$_logDir/$_log" > "$_log"
        tail -n 400 "$_logDir/$_log" > "$_log.tail"
        rm -f "$_logDir/$_log"
    else
        mv "$_logDir/$_log" "$_log"
    fi
    rmdir "$_logDir"

    return $_status
}
