FROM python:3.8

ENV _WORKDIR=/srv/pansen

RUN mkdir -p ${_WORKDIR}
COPY . ${_WORKDIR}/
WORKDIR ${_WORKDIR}
RUN make bootstrap build

# Ensure we can call our own scripts without any prefix
ENV PATH=${_WORKDIR}/.venv/bin:$PATH

EXPOSE 8000
ENTRYPOINT [ "pansen_aiven" ]

