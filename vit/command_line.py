from vit import parse_options, Application

def main():
    options, filters = parse_options()
    Application(options, filters)

if __name__ == '__main__':
    main()
