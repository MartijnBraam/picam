package ipc

import (
	"bytes"
	"encoding/binary"
	"errors"
	"fmt"
	"net"
	"os"
	"time"
)

type IPCClient struct {
	conn *net.UnixConn
}

func New() (*IPCClient, error) {
	fname := "/tmp/sensor-control"
	for _ = range 60 {
		if _, err := os.Stat(fname); errors.Is(err, os.ErrNotExist) {
			fmt.Println("Control socket does not exist yet, waiting")
			time.Sleep(1 * time.Second)
		} else {
			break
		}
	}

	conn, err := net.DialUnix("unixpacket", nil, &net.UnixAddr{
		Name: fname,
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

func (c *IPCClient) SetTally(tally byte) {
	payload := []byte{0x05, tally}
	c.conn.Write(payload)
}

func (c *IPCClient) SetGain(gain byte) {
	payload := []byte{0x06, gain}
	fmt.Printf("SET GAIN %v\n", payload)
	c.conn.Write(payload)
}

func (c *IPCClient) SetShutter(shutter uint16) {
	var buf bytes.Buffer
	binary.Write(&buf, binary.LittleEndian, byte(0x07))
	binary.Write(&buf, binary.LittleEndian, shutter)
	b := buf.Bytes()
	c.conn.Write(b)
}

func (c *IPCClient) SetFPS(fps byte) {
	payload := []byte{0x08, fps}
	c.conn.Write(payload)
}

func (c *IPCClient) SetExposureCompensation(ec float32) {
	var buf bytes.Buffer
	binary.Write(&buf, binary.LittleEndian, byte(0x09))
	binary.Write(&buf, binary.LittleEndian, ec)
	b := buf.Bytes()
	c.conn.Write(b)
}
