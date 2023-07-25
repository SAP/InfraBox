FROM public.ecr.aws/docker/library/alpine

RUN apk add --no-cache python3 py3-requests py3-pip curl

COPY . project

CMD ["project/infrabox/test/entrypoint.sh"]
