#!/bin/sh

set -e
set -u

TMP_DIR="$(mktemp --directory --suffix .vit)"
VIT_DIR="$TMP_DIR/vit"
TASK_DIR="$TMP_DIR/task"
TASKRC="$TMP_DIR/taskrc"

echo "
This script will create a dummy TaskWarrior database and VIT configuration.
"
read -p "Press enter to continue... " DUMMY

echo "Creating dummy task configuration..."
mkdir "$TASK_DIR"
cat > "$TASKRC" <<EOT
data.location=$TASK_DIR
EOT
export TASKRC

echo "Creating dummy VIT configuration..."
mkdir "$VIT_DIR"
touch "$VIT_DIR/config.ini"

echo "Adding some dummy tasks..."
task add a
task add b
task +LATEST start
task add c
task +LATEST start

echo "Complete!

Copy and paste the following two export statements into your current
shell sesison to activate the dummy installation.

export TASKRC=${TASKRC}
export VIT_DIR=${VIT_DIR}

When complete, you can simply exit the current shell session, or copy and paste
the following 'unset' commands to revert the current shell session to the
TaskWarrior/VIT defaults.

unset TASKRC
unset VIT_DIR
"
