from pysproto.sproto import SprotoType
from pysproto.sproto_exception import SprotoException


def word_to_int(word: bytes):
    # little end
    return word[0] + word[1]*256


def dword_to_int(dword: bytes):
    return dword[0] + dword[1]*256 + dword[2] * 256 * 256 + dword[3] * 256 * 256 * 256


class SprotoEncoder:

    @staticmethod
    def encode_string(src: str) -> bytes:
        header = bytearray(src.__len__().to_bytes(4, 'little'))
        data = src.encode('utf-8')
        header.extend(data)
        return header

    @staticmethod
    def encode_desc_int(src: int) -> bytes:
        return ((src+1)*2).to_bytes(2, 'little')

    @staticmethod
    def encode(proto_type: SprotoType, data: dict) -> bytes:
        count = 0
        desc = bytearray()
        data_section = bytearray()
        current_tag = 0
        for field in proto_type.members():
            tag = field.tag()
            type_name = field.type_name()
            data_type = field.type()
            content = data.get(type_name)

            if tag < current_tag:
                raise SprotoException(
                    'tag sequence wrong! {}->{}'.format(current_tag, tag))
            if content is None:
                continue

            if tag > current_tag:
                skipped = tag - current_tag
                desc.extend((skipped*2-1).to_bytes(2, 'little'))

            current_tag = tag + 1

            if data_type == int:
                tmp = int(content)
                desc.extend(SprotoEncoder.encode_desc_int(tmp))
            elif data_type == str:
                tmp = str(content)
                desc.extend(b'\x00\x00')
                data_section.extend(SprotoEncoder.encode_string(tmp))
            elif data_type.__qualname__ == 'list':
                tmp = list(content)
                desc.extend(b'\x00\x00')
                list_sz = 0
                tmp_encoded = bytearray()
                member_type = None
                for member in tmp:
                    encoded = bytes()
                    member_type = type(member)
                    # TODO: implement int64, struct, boolean
                    if member_type == str:
                        encoded = SprotoEncoder.encode_string(member)
                    elif member_type == int:
                        encoded = int(member).to_bytes(4, 'little')
                    tmp_encoded.extend(encoded)
                    list_sz += encoded.__len__()

                if member_type == int:
                    list_sz += 1
                data_section.extend(list_sz.to_bytes(4, 'little'))
                if member_type == int:
                    data_section.extend(int(4).to_bytes(1, 'little'))
                data_section.extend(tmp_encoded)

            count += 1
        rs = bytearray(count.to_bytes(2, 'little'))
        rs.extend(desc)
        rs.extend(data_section)
        return rs

    @staticmethod
    def decode(sproto_type: SprotoType, data: bytes):
        current_i: int = 0
        current_tag: int = 0
        data_section_count: int = 0
        data_section_tag_names = []
        data_section_tag_types = []
        rs = {}

        header_sz = word_to_int(data[current_i:current_i+2])
        current_i += 2
        for i in range(0, header_sz):
            tmp = word_to_int(data[current_i:current_i+2])
            current_i += 2
            if tmp % 2 == 1:
                # skipped tags
                current_tag += (tmp+1)//2
                continue

            tag_name = sproto_type.member(current_tag).type_name()
            tag_type = sproto_type.member(current_tag).type()
            current_tag += 1

            if tmp == 0:
                # data in data section
                data_section_count += 1
                data_section_tag_names.append(tag_name)
                data_section_tag_types.append(tag_type)
                continue

            val = tmp // 2 - 1
            rs[tag_name] = val

            
        for i in range(0, data_section_count):
            data_sz = dword_to_int(data[current_i:current_i+4])
            current_i += 4
            tag_name = data_section_tag_names[i]
            tag_type = data_section_tag_types[i]
            val = None
            if tag_type == str:
                val = data[current_i:current_i+data_sz].decode('utf-8')
            elif tag_type.__qualname__ == 'list':
                if tag_type == list[str]:
                    val = []
                    tmp_i = current_i
                    while tmp_i < current_i + data_sz:
                        str_len = dword_to_int(data[tmp_i:tmp_i+4])
                        decoded = data[tmp_i+4: tmp_i +
                                       4+str_len].decode('utf-8')
                        val.append(decoded)
                        tmp_i += 4+str_len
                elif tag_type == list[int]:
                    val = []
                    tmp_i = current_i
                    int_len = data[tmp_i]
                    tmp_i += 1
                    while tmp_i < current_i + data_sz:
                        decoded = word_to_int(data[tmp_i:tmp_i+int_len])
                        tmp_i += int_len
                        val.append(decoded)

            current_i += data_sz
            rs[tag_name] = val
        return rs, current_i

    @staticmethod
    def zero_pack(src: bytes) -> bytes:
        i = 0
        rs = bytearray()
        while i < src.__len__():
            pack_byte = 0
            body = bytearray()
            start = i
            end = i+7
            if i + 7 >= src.__len__():
                end = src.__len__() - 1
            for j in range(start, end+1):
                if src[j] != 0:
                    pack_byte += 2**(j - start)
                    body.append(src[j])
            rs.extend(pack_byte.to_bytes(1, 'little'))
            if pack_byte == 0xff:
                # handle the continous un-zero
                unzero_count = 0
                while True:
                    start = end + 1
                    end = start + 7
                    if end >= src.__len__():
                        end -= 8
                        break
                    zero_count = 0
                    for j in range(start, end+1):
                        if src[j] == 0:
                            zero_count += 1
                    if zero_count >= 3:
                        end -= 8
                        break
                    else:
                        unzero_count += 1
                        for j in range(start, end+1):
                            body.append(src[j])

                rs.extend(unzero_count.to_bytes(1, 'little'))

            rs.extend(body)
            i = end+1
        return rs

    @staticmethod
    def zero_unpack(src: bytes) -> bytes:
        i = 0
        rs = bytearray()
        while i < src.__len__():
            # unpack for each 9 bytes
            pack_int = src[i]
            body = bytearray()
            current_data_i = i+1
            if pack_int == 0xff:
                unzero_count = src[i+1].as_integer_ratio()[0]+1
                current_data_i += 1
                for j in range(0, unzero_count):
                    body.extend(src[current_data_i:current_data_i + 8])
                    current_data_i += 8
            else:
                for j in range(0, 8):
                    remainder = pack_int % 2
                    pack_int = pack_int // 2
                    if remainder == 0:
                        body.extend(b'\x00')
                    else:
                        body.append(src[current_data_i])
                        current_data_i += 1
            rs.extend(body)
            i = current_data_i

        return rs

    @staticmethod
    def length_pack(src: bytes) -> bytes:
        len = src.__len__()
        len_bytes = len.to_bytes(2, 'little')
        rs = bytearray(src)
        for i in range(0, len_bytes.__len__()):
            rs.insert(0, len_bytes[i])
        return rs

    @staticmethod
    def length_unpack(src: bytes) -> bytes:
        len = src[0] + src[1]
        rs = bytes(src[2:src.__len__()])
        return rs
