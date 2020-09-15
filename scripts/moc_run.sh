#!/bin/bash

IMAGE="moc"

echo "Run image ${IMAGE}"
sudo docker run --rm -v ${PWD}:/usr/src/app/ ${IMAGE} ${IMAGE}_run || exit $?

date
exit 0

