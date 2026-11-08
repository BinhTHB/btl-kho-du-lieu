"""Dữ liệu mẫu được nạp thẳng vào SQL Server bởi mockup_generator."""


def main() -> None:
    from mockup_generator.generate_sample_data import nap_mau

    nap_mau()


if __name__ == "__main__":
    main()
