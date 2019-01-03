FROM golang:1.11

EXPOSE 8000

ADD main.go /main.go
ADD go.mod /go.mod
ADD go.sum /go.sum

RUN go mod download

ENTRYPOINT ["go", "run", "/main.go"]