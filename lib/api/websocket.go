package api

import (
	"fmt"
	"log"
	"net/http"
	"time"

	"github.com/gorilla/websocket"
)

type Client struct {
	hub  *Hub
	conn *websocket.Conn
	send chan []byte
	cam  *APIServer
}

func (c *Client) writer() {
	defer func() {
		c.conn.Close()
	}()

	for {
		select {
		case message, ok := <-c.send:
			c.conn.SetWriteDeadline(time.Now().Add(10 * time.Second))
			if !ok {
				c.conn.WriteMessage(websocket.CloseMessage, []byte{})
				return
			}

			w, err := c.conn.NextWriter(websocket.TextMessage)
			if err != nil {
				return
			}
			w.Write(message)

			if err := w.Close(); err != nil {
				return
			}
		}
	}
}

func (c *Client) sendProperties() {
	response := &WebsocketMessage{
		Type: "response",
		Data: ListProperties{
			Action: "listProperties",
			Properties: []string{
				"/video/gain",
				"/video/shutter",
				"/video/whiteBalance",
				"/video/autoExposure",
				"/colorCorrection/lift",
				"/colorCorrection/gamma",
				"/colorCorrection/gain",
				"/colorCorrection/offset",
			},
		},
	}
	err := c.conn.WriteJSON(response)
	if err != nil {
		panic(err)
	}
}

func (c *Client) sendMessage(wm *WebsocketMessage) {
	c.conn.WriteJSON(wm)
}

func (c *Client) subscribe(property string) {
	switch property {
	case "/video/autoExposure":
		c.sendMessage(&WebsocketMessage{
			Type: "event",
			Data: &PropertyChanged{
				Action:   "propertyValueChanged",
				Property: "/video/autoExposure",
				Value:    c.cam.state.AutoExposure,
			},
		})
	case "/video/gain":
		c.sendMessage(&WebsocketMessage{
			Type: "event",
			Data: &PropertyChanged{
				Action:   "propertyValueChanged",
				Property: "/video/gain",
				Value:    c.cam.state.Gain,
			},
		})
	case "/video/shutter":
		c.sendMessage(&WebsocketMessage{
			Type: "event",
			Data: &PropertyChanged{
				Action:   "propertyValueChanged",
				Property: "/video/shutter",
				Value:    c.cam.state.Shutter,
			},
		})
	case "/video/whiteBalance":
		c.sendMessage(&WebsocketMessage{
			Type: "event",
			Data: &PropertyChanged{
				Action:   "propertyValueChanged",
				Property: "/video/whiteBalance",
				Value:    c.cam.state.WhiteBalance,
			},
		})
	case "/colorCorrection/lift":
		c.sendMessage(&WebsocketMessage{
			Type: "event",
			Data: &PropertyChanged{
				Action:   "propertyValueChanged",
				Property: "/colorCorrection/lift",
				Value:    c.cam.state.CCLift,
			},
		})
	case "/colorCorrection/gamma":
		c.sendMessage(&WebsocketMessage{
			Type: "event",
			Data: &PropertyChanged{
				Action:   "propertyValueChanged",
				Property: "/colorCorrection/gamma",
				Value:    c.cam.state.CCGamma,
			},
		})
	case "/colorCorrection/gain":
		c.sendMessage(&WebsocketMessage{
			Type: "event",
			Data: &PropertyChanged{
				Action:   "propertyValueChanged",
				Property: "/colorCorrection/gain",
				Value:    c.cam.state.CCGain,
			},
		})
	case "/colorCorrection/offset":
		c.sendMessage(&WebsocketMessage{
			Type: "event",
			Data: &PropertyChanged{
				Action:   "propertyValueChanged",
				Property: "/colorCorrection/offset",
				Value:    c.cam.state.CCOffset,
			},
		})
	}
}

func (c *Client) reader() {
	defer func() {
		c.hub.unregister <- c
		c.conn.Close()
	}()
	for {
		var msg WebsocketMessage
		err := c.conn.ReadJSON(&msg)
		if err != nil {
			break
		}
		switch msg.Type {
		case "request":
			action := msg.Data.(map[string]interface{})["action"].(string)
			switch action {
			case "listProperties":
				c.sendProperties()
			case "subscribe":
				props := msg.Data.(map[string]interface{})["properties"].([]interface{})
				for _, prop := range props {
					c.subscribe(prop.(string))
				}
			default:
				fmt.Println("Unknown request:", action)
			}
		default:
			fmt.Println("Unknown type:", msg.Type)
		}
		fmt.Println("MESAGES", msg)
	}
}

var upgrader = websocket.Upgrader{
	HandshakeTimeout: 0,
	ReadBufferSize:   1024,
	WriteBufferSize:  1024,
	WriteBufferPool:  nil,
	Subprotocols:     nil,
	Error:            nil,
	CheckOrigin: func(r *http.Request) bool {
		return true
	},
	EnableCompression: false,
}

func (s *APIServer) EventWebsocket(w http.ResponseWriter, r *http.Request) {
	fmt.Println("Websocket Event")
	ws, err := upgrader.Upgrade(w, r, nil)
	if err != nil {
		if _, ok := err.(websocket.HandshakeError); !ok {
			log.Println(err)
		}
		return
	}

	client := &Client{
		hub:  s.hub,
		conn: ws,
		send: make(chan []byte, 256),
		cam:  s,
	}
	s.hub.register <- client

	go client.writer()
	go client.reader()
}
