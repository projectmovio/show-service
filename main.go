package main

import (
	"encoding/json"
	"github.com/gorilla/mux"
	"log"
	"net/http"
)

var temp = [2]TempStruct{TempStruct{1, "abc"}, TempStruct{2, "cde"}}

func main() {
	log.Print(temp)
	router := mux.NewRouter()
	router.HandleFunc("/test", Test).Methods("GET")
	log.Fatal(http.ListenAndServe(":8000", router))
}

func Test(w http.ResponseWriter, r *http.Request) {
	json.NewEncoder(w).Encode(temp)
}

type TempStruct struct {
	ID  int    `json:"id,omitempty"`
	Val string `json:"val,omitempty"`
}