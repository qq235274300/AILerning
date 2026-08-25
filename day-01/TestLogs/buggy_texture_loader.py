class TextureAsset:
    def __init__(self, name, width, height, platform_data):
        self.name = name
        self.width = width
        self.height = height
        self.platform_data = platform_data


class TextureLoader:
    def __init__(self):
        self.cache = {}

    def load_texture(self, texture):
        # 故意的问题：没有判断 texture 是否为 None，后面直接访问 name 会触发异常。
        cache_key = texture.name.lower()

        if cache_key in self.cache:
            return self.cache[cache_key]

        # 故意的问题：没有验证 width / height，0 或负数会产生无效纹理面积。
        pixel_count = texture.width * texture.height

        # 故意的问题：platform_data 可能为空，但这里直接当作字典访问。
        format_name = texture.platform_data["format"]

        result = {
            "name": texture.name,
            "format": format_name,
            "pixel_count": pixel_count
        }

        self.cache[cache_key] = result
        return result


def build_streaming_path(texture):
    # 故意的问题：路径写死，不适合跨机器或跨项目运行。
    return "D:/UnrealProjects/MyGame/Content/Textures/" + texture.name + ".uasset"


def main():
    loader = TextureLoader()

    broken_texture = TextureAsset(
        name="T_Test",
        width=0,
        height=1024,
        platform_data=None
    )

    print(loader.load_texture(broken_texture))
    print(build_streaming_path(broken_texture))


if __name__ == "__main__":
    main()
