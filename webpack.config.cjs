const path = require("path");
const HtmlBundlerPlugin = require("html-bundler-webpack-plugin");

let baseConfig = {
  entry: {},
  output: {
    path: path.resolve(__dirname, "src", "fontra_rcjk", "client"),
    publicPath: "rcjk/",
    clean: true,
    filename: "[name].js",
  },
  mode: "development",
  experiments: {
    asyncWebAssembly: true,
  },
  resolve: {
    extensionAlias: {
      ".js": [".ts", ".js"],
    },
  },
  module: {
    rules: [
      {
        test: /\.s?css$/,
        use: ["css-loader"],
      },
      {
        test: /\.(ico|png|jp?g|svg)/,
        type: "asset/resource",
      },
      {
        test: /\.tsx?$/,
        loader: "babel-loader",
        exclude: /node_modules/,
        options: {
          presets: ["@babel/preset-env", "@babel/preset-typescript"],
        },
      },
    ],
  },
  resolve: {
    modules: [path.resolve(__dirname, "node_modules")],
    fallback: {
      fs: false,
      zlib: false,
      assert: false,
      util: false,
      stream: false,
      path: false,
      url: false,
      buffer: require.resolve("buffer"),
    },
  },
  plugins: [
    new HtmlBundlerPlugin({
      entry: {
        landing: path.resolve(
          __dirname,
          "src-js",
          "projectmanager-rcjk",
          "landing.html"
        ),
      },
    }),
  ],
};

module.exports = (env, argv) => {
  if (argv.mode === "production") {
    baseConfig.mode = "production";
    baseConfig.output.filename = "[name].[contenthash:8].js";
  } else {
    baseConfig.devtool = "eval-source-map";
  }
  return baseConfig;
};
