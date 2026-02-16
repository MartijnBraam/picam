package ipc

import (
	"net"
)

type IPCClient struct {
	conn *net.UnixConn
}

func New() (*IPCClient, error) {
	conn, err := net.DialUnix("unixpacket", nil, &net.UnixAddr{
		Name: "/tmp/sensor-control",
		Net:  "unixpacket",
	})
	if err != nil {
		return nil, err
	}
	return &IPCClient{conn: conn}, nil
}

func (c *IPCClient) RequestState() error {
	buf := []byte{0x01}
	_, err := c.conn.Write(buf)
	return err
}

func (c *IPCClient) Read() ([]byte, error) {
	readbuffer := make([]byte, 1024)
	size, err := c.conn.Read(readbuffer)
	if err != nil {
		return nil, err
	}
	//log.Println("Received", readbuffer[:size])
	return readbuffer[:size], nil
}

func (c *IPCClient) EnableAutoExposure(enabled bool) {
	payload := []byte{0x02, 0x00}
	if enabled {
		payload[1] = 0x01
	}
	c.conn.Write(payload)
}

func (c *IPCClient) EnableAutoWhitebalance(enabled bool) {
	payload := []byte{0x03, 0x00}
	if enabled {
		payload[1] = 0x01
	}
	c.conn.Write(payload)
}

func (c *IPCClient) DoAutoWhitebalance() error {
	buf := []byte{0x04}
	_, err := c.conn.Write(buf)
	return err
}
