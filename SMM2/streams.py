import struct
import codecs

class StreamIn:
    def __init__(self, data=None):
        self.position = 0
        self.byteorder = codecs.BOM_UTF16_BE
        if not data:
            return None
        else:
            self.load(data)

    def load(self, data=None):
        if not data:
            return None
        else:
            self.data = data

    def substream(self, length=1, byteorder=None):
        if not byteorder:
            read = self.read(length)
        else:
            if byteorder == codecs.BOM_UTF16_BE:
                read = self.read(length, codecs.BOM_UTF16_BE)
            elif byteorder == codecs.BOM_UTF16_LE:
                read = self.read(length, codecs.BOM_UTF16_LE)
            else:
                return None
        return StreamIn(read)

    def seek(self, pos=None):
        if pos is None:
            return None
        else:
            self.position = pos

    def skip(self, length=None):
        if not length:
            return None
        else:
            self.seek(self.position + length)

    def read(self, length=None, byteorder=None):
        if not length:
            return False
        else:
            read = self.data[ self.position : self.position + length ]
            self.position += length
        if not byteorder:
            if self.byteorder == codecs.BOM_UTF16_BE:
                return read
            elif self.byteorder == codecs.BOM_UTF16_LE:
                chunks = []
                for i in range(read.__len__()):
                    chunks.append(read[ (len(read)-i)-1 : (len(read)-i) ])
                return bytes.join(b"", chunks)
            else:
                return None
        else:
            if byteorder == codecs.BOM_UTF16_BE:
                return read
            elif byteorder == codecs.BOM_UTF16_LE:
                chunks = []
                for i in range(read.__len__()):
                    chunks.append(read[ (len(read)-i)-1 : (len(read)-i) ])
                return bytes.join(b"", chunks)
            else:
                return None

    def read8(self):
        read = self.read(1)
        if not read.__len__() == 1:
            return None
        else:
            return struct.unpack(">B", read)[0]

    def read16(self, byteorder=None):
        if not byteorder:
            read = self.read(2)
        else:
            read = self.read(2, byteorder)
        if not read.__len__() == 2:
            return None
        else:
            return struct.unpack(">H", read)[0]

    def read32(self, byteorder=None):
        if not byteorder:
            read = self.read(4)
        else:
            read = self.read(4, byteorder)
        if not read.__len__() == 4:
            return None
        else:
            return struct.unpack(">I", read)[0]

    def read64(self, byteorder=None):
        if not byteorder:
            read = self.read(8)
        else:
            read = self.read(8, byteorder)
        if not read.__len__() == 8:
            return None
        else:
            return struct.unpack(">Q", read)[0]

class StreamOut:
    def __init__(self, data=None):
        self.byteorder = codecs.BOM_UTF16_BE
        if not data:
            self.chunks = []
        else:
            self.chunks = [data]

    def data(self):
        return bytes.join(b"", self.chunks)

    def write(self, data=None, byteorder=None):
        if not data:
            return None
        else:
            if not byteorder:
                if self.byteorder == codecs.BOM_UTF16_BE:
                    self.chunks.append(data)
                elif self.byteorder == codecs.BOM_UTF16_LE:
                    chunks = []
                    for i in range(read.__len__()):
                        chunks.append(read[ (len(read)-i)-1 : (len(read)-i) ])
                    self.chunks.append(bytes.join(b"", chunks))
                else:
                    return None
            else:
                if byteorder == codecs.BOM_UTF16_BE:
                    self.chunks.append(data)
                elif byteorder == codecs.BOM_UTF16_LE:
                    chunks = []
                    for i in range(read.__len__()):
                        chunks.append(read[ (len(read)-i)-1 : (len(read)-i) ])
                    self.chunks.append(bytes.join(b"", chunks))
                else:
                    return None
        

    def write8(self, value=None):
        if value is None:
            return None
        else:
            self.chunks.append(struct.pack(">B", value))

    def write16(self, value=None, byteorder=None):
        if value is None:
            return None
        else:
            if not byteorder:
                if self.byteorder == codecs.BOM_UTF16_BE:
                    self.chunks.append(struct.pack(">H", value))
                elif self.byteorder == codecs.BOM_UTF16_LE:
                    self.chunks.append(struct.pack("<H", value))
            else:
                if byteorder == codecs.BOM_UTF16_BE:
                    self.chunks.append(struct.pack(">H", value))
                elif byteorder == codecs.BOM_UTF16_LE:
                    self.chunks.append(struct.pack("<H", value))

    def write32(self, value=None, byteorder=None):
        if value is None:
            return None
        else:
            if not byteorder:
                if self.byteorder == codecs.BOM_UTF16_BE:
                    self.chunks.append(struct.pack(">I", value))
                elif self.byteorder == codecs.BOM_UTF16_LE:
                    self.chunks.append(struct.pack("<I", value))
            else:
                if byteorder == codecs.BOM_UTF16_BE:
                    self.chunks.append(struct.pack(">I", value))
                elif byteorder == codecs.BOM_UTF16_LE:
                    self.chunks.append(struct.pack("<I", value))

    def write64(self, value=None, byteorder=None):
        if value is None:
            return None
        else:
            if not byteorder:
                if self.byteorder == codecs.BOM_UTF16_BE:
                    self.chunks.append(struct.pack(">Q", value))
                elif self.byteorder == codecs.BOM_UTF16_LE:
                    self.chunks.append(struct.pack("<Q", value))
            else:
                if byteorder == codecs.BOM_UTF16_BE:
                    self.chunks.append(struct.pack(">Q", value))
                elif byteorder == codecs.BOM_UTF16_LE:
                    self.chunks.append(struct.pack("<Q", value))
