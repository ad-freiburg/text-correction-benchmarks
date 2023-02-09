.PHONY: zip_benchmarks
zip_benchmarks:
	cd benchmarks && zip -r ../benchmarks.zip . -x "./*/*/*/predictions/*"
	cd benchmarks && zip -r ../benchmarks_with_predictions.zip .
