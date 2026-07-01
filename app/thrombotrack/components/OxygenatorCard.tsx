// Oxygenator card displayed in home screen list

import MaterialCommunityIcons from "@expo/vector-icons/MaterialCommunityIcons";
import { Picker } from "@react-native-picker/picker";
import { Image } from "expo-image";
import * as ImagePicker from "expo-image-picker";
import { useRouter } from "expo-router";
import moment from "moment";
import { FC, JSX, useState } from "react";
import {
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from "react-native";

import * as Colors from "@/constants/colors";
import { Oxygenator, OxygenatorType } from "@/constants/types";
import { useStateContext } from "@/context/StateContext";

type OxygenatorCardProps = {
  oxygenator: Oxygenator;
  createOxygenator: (name: string) => void;
  editOxygenator: (
    oxygenatorId: string,
    payload: Pick<Partial<Oxygenator>, "name" | "type">,
  ) => void;
  deleteOxygenator: (oxygenatorId?: string) => void;
};

/**
 * Card for an oxygenator in home screen list.
 *
 * Handles editing oxygenator name, changing the type, uploading images, navigating to
 * chart/gallery, and deleting.
 *
 * @param props Oxygenator item and functions for creating, editing, and deleting oxygenators.
 *
 * @returns Card component
 */
const OxygenatorCard: FC<OxygenatorCardProps> = ({
  oxygenator,
  createOxygenator,
  editOxygenator,
  deleteOxygenator,
}): JSX.Element => {
  const router = useRouter();
  const { dispatch } = useStateContext();

  const [newName, setNewName] = useState<string>(""); // new name input while editing
  const [isEditing, setIsEditing] = useState(false);

  const isNautilus = oxygenator.type === OxygenatorType.NAUTILUS;
  const isUnsaved = oxygenator.id === undefined;

  const totalBurden =
    (oxygenator.clot_area ?? 0) + (oxygenator.fibrin_area ?? 0);
  const clotPercent =
    ((oxygenator.clot_area ?? 0) / Math.max(totalBurden, 1)) * 100;
  const fibrinPercent =
    ((oxygenator.fibrin_area ?? 0) / Math.max(totalBurden, 1)) * 100;

  // Enables editing name.
  const doPressName = (): void => {
    setIsEditing(true);
  };

  /**
   * Handles name input being blurred.π
   *
   * If this is an unsaved oxygenator, either creates the oxygenator or deletes it (if input is
   * empty). Otherwise, edits the name.
   */
  const doBlurName = (): void => {
    if (newName.length === 0) {
      if (isUnsaved) {
        deleteOxygenator(oxygenator.id);
      }
    } else if (isUnsaved) {
      createOxygenator(newName);
    } else if (newName !== oxygenator.name) {
      editOxygenator(oxygenator.id!, { name: newName });
    }
    setIsEditing(false);
  };

  /**
   * Changes type of oxygenator.
   *
   * @param type New type of oxygenator
   */
  const doChangeType = (type: OxygenatorType): void => {
    editOxygenator(oxygenator.id!, { type });
  };

  /**
   * Renders area value.
   *
   * If area is 0, returns "0". If area is greater than 10 mm², returns in cm². Otherwise,
   * returns to two decimal places.
   *
   * @param area Area value
   *
   * @returns Parsed area string
   */
  const renderArea = (area: number | null): string => {
    if (area === null || area === 0) {
      return "0";
    }

    if (area > 10) {
      return (area / 100).toFixed(2);
    }

    return area.toFixed(2);
  };

  /**
   * Renders area units label.
   *
   * @param area Area value
   *
   * @returns mm² or cm².
   */
  const getAreaLabel = (area: number | null): string => {
    if (area === null || area === 0) {
      return "mm²";
    }

    if (area > 10) {
      return "cm²";
    }

    return "mm²";
  };

  // Navigates to gallery screen
  const doPressGallery = (): void => {
    router.navigate({
      pathname: "/gallery",
      params: { oxygenatorId: oxygenator.id! },
    });
  };

  // Navigates to chart screen
  const doPressChart = (): void => {
    router.navigate({
      pathname: "/chart",
      params: { oxygenatorId: oxygenator.id! },
    });
  };

  // Launches the device image picker and saves the file in state context.
  const doPressCamera = async (): Promise<void> => {
    if (dispatch === null) {
      return;
    }

    ImagePicker.launchImageLibraryAsync({ allowsEditing: true }).then(
      (result) => {
        if (result.canceled) {
          return;
        }

        const { file } = result.assets[0];

        if (file === undefined) {
          window.alert("Image not found, please try again");
          return;
        }

        dispatch({ type: "SET_FILE", payload: file });
        router.navigate({
          pathname: "/annotate",
          params: {
            oxygenatorId: oxygenator.id,
            oxygenatorType: oxygenator.type,
          },
        });
      },
    );
  };

  // Deletes an oxygenator with confirmation
  const doPressDelete = (): void => {
    const response = window.confirm(
      "Are you sure you want to delete this oxygenator?\nAll images and annotations will be deleted.",
    );

    if (response) {
      deleteOxygenator(oxygenator.id);
    }
  };

  // Action buttons to display at bottom of card
  const actions = [
    {
      id: "gallery",
      icon: "image-multiple",
      color: Colors.INDIGO,
      onPress: doPressGallery,
    },
    {
      id: "chart",
      icon: "chart-line",
      color: Colors.GREEN,
      onPress: doPressChart,
    },
    {
      id: "upload-image",
      icon: "camera",
      color: Colors.BLUE,
      onPress: doPressCamera,
    },
    {
      id: "delete",
      icon: "trash-can",
      color: Colors.RED,
      onPress: doPressDelete,
    },
  ];

  return (
    <View style={styles.card}>
      <View style={styles.header}>
        {isUnsaved || isEditing ? (
          // Input to edit name field
          <TextInput
            autoFocus
            defaultValue={oxygenator.name}
            onBlur={doBlurName}
            onChangeText={setNewName}
            placeholder="Enter name..."
            placeholderTextColor={Colors.GRAY_4}
            style={styles.nameInput}
          />
        ) : (
          // Name
          <TouchableOpacity onPress={doPressName} style={styles.nameContainer}>
            <Text style={styles.name}>{oxygenator.name}</Text>
            <MaterialCommunityIcons
              name="pencil"
              size={18}
              color={Colors.GRAY}
              style={styles.editIcon}
            />
          </TouchableOpacity>
        )}

        {/* Type (HLS/Nautilus picker) */}
        <Picker
          onValueChange={doChangeType}
          selectedValue={oxygenator.type}
          style={styles.picker}
        >
          <Picker.Item label="HLS" value={OxygenatorType.HLS} />
          <Picker.Item label="Nautilus" value={OxygenatorType.NAUTILUS} />
        </Picker>
      </View>

      <View style={styles.body}>
        {/* Last annotation */}
        <View style={styles.lastAnnotation}>
          {/* Current area */}
          <View style={styles.totalRow}>
            <Text style={styles.totalValue}>{renderArea(totalBurden)}</Text>
            <Text style={styles.totalUnit}>{getAreaLabel(totalBurden)}</Text>
            <Text style={styles.totalLabel}>total burden</Text>
          </View>

          {/* Bar */}
          <View style={styles.burdenTrack}>
            <View style={[styles.clottingBar, { width: `${clotPercent}%` }]} />
            <View style={[styles.fibrinBar, { width: `${fibrinPercent}%` }]} />
          </View>

          {/* Clot/fibrin breakdown */}
          <View style={styles.breakdown}>
            <View style={styles.breakdownItem}>
              <Text
                style={[styles.breakdownValue, { color: Colors.CHART_RED }]}
              >
                {renderArea(oxygenator.clot_area)}{" "}
                {getAreaLabel(oxygenator.clot_area)}
              </Text>
              <View style={styles.breakdownLabelContainer}>
                <View
                  style={[
                    styles.breakdownDot,
                    { backgroundColor: Colors.CHART_RED },
                  ]}
                />
                <Text style={styles.breakdownLabel}>Clotting</Text>
              </View>
            </View>

            <View style={styles.breakdownDivider} />

            <View style={styles.breakdownItem}>
              <Text
                style={[styles.breakdownValue, { color: Colors.CHART_BLUE }]}
              >
                {renderArea(oxygenator.fibrin_area)}{" "}
                {getAreaLabel(oxygenator.fibrin_area)}
              </Text>
              <View style={styles.breakdownLabelContainer}>
                <View
                  style={[
                    styles.breakdownDot,
                    { backgroundColor: Colors.CHART_BLUE },
                  ]}
                />
                <Text style={styles.breakdownLabel}>Fibrin</Text>
              </View>
            </View>
          </View>

          {oxygenator.imaged_at !== null && oxygenator.annotated_by !== null ? (
            <Text style={styles.lastImaged}>
              {moment(oxygenator.imaged_at).format("M/D HH:mm")} by{" "}
              {oxygenator.annotated_by}
            </Text>
          ) : null}
        </View>

        {/* Thumbnail */}
        {oxygenator.thumbnail !== null ? (
          <TouchableOpacity onPress={doPressGallery}>
            <Image
              source={oxygenator.thumbnail}
              style={[styles.image, { borderRadius: isNautilus ? 70 : 10 }]}
            />
          </TouchableOpacity>
        ) : (
          <TouchableOpacity
            onPress={doPressCamera}
            style={[
              styles.image,
              styles.imagePlaceholder,
              { borderRadius: isNautilus ? 70 : 10 },
            ]}
          >
            {!isUnsaved ? (
              <MaterialCommunityIcons
                name="camera"
                size={24}
                color={Colors.WHITE}
              />
            ) : null}
          </TouchableOpacity>
        )}
      </View>

      {/* Actions */}
      {!isUnsaved ? (
        <View style={styles.actionsRow}>
          {actions.map((action) => (
            <TouchableOpacity
              key={action.id}
              onPress={action.onPress}
              style={[
                styles.action,
                {
                  backgroundColor: `${action.color}4d`,
                  boxShadow: `0px 0px 10px 0px ${action.color}1a`,
                },
              ]}
            >
              <MaterialCommunityIcons
                // @ts-ignore
                name={action.icon}
                size={20}
                color={action.color}
              />
            </TouchableOpacity>
          ))}
        </View>
      ) : null}
    </View>
  );
};

const styles = StyleSheet.create({
  card: {
    backgroundColor: "white",
    borderRadius: 15,
    padding: 10,
  },
  header: {
    display: "flex",
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    gap: 10,
  },
  nameInput: {
    borderRadius: 8,
    padding: 5,
    width: "100%",
    fontWeight: 500,
    fontSize: 23,
    marginRight: 10,
    marginLeft: -5,
  },
  nameContainer: {
    display: "flex",
    alignItems: "center",
    flexDirection: "row",
    flex: 1,
  },
  name: {
    fontWeight: 500,
    fontSize: 23,
    borderWidth: 5,
    borderColor: "transparent",
    marginLeft: -5,
  },
  editIcon: {
    marginLeft: 5,
  },
  picker: {
    height: 30,
    fontWeight: 500,
    fontSize: 12,
    paddingHorizontal: 10,
    borderRadius: 12,
  },
  totalRow: {
    flexDirection: "row",
    alignItems: "baseline",
    gap: 4,
  },
  totalValue: {
    fontSize: 26,
    fontWeight: "700",
    letterSpacing: -0.5,
  },
  totalUnit: {
    fontSize: 13,
    fontWeight: "600",
    color: Colors.GRAY,
  },
  totalLabel: {
    fontSize: 12,
    marginLeft: 4,
    color: Colors.GRAY,
  },
  body: {
    display: "flex",
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
  },
  lastAnnotation: {
    display: "flex",
    flex: 1,
  },
  burdenTrack: {
    flexDirection: "row",
    height: 5,
    borderRadius: 3,
    backgroundColor: Colors.GRAY_5,
    overflow: "hidden",
    marginTop: 8,
    marginBottom: 2,
  },
  fibrinBar: { height: 5, backgroundColor: Colors.CHART_BLUE },
  clottingBar: { height: 5, backgroundColor: Colors.CHART_RED },
  breakdown: {
    flexDirection: "row",
    alignItems: "center",
    marginTop: 8,
    marginBottom: 12,
  },
  breakdownItem: {
    flex: 1,
  },
  breakdownLabelContainer: {
    display: "flex",
    flexDirection: "row",
    alignItems: "center",
    gap: 5,
  },
  breakdownDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
  },
  breakdownLabel: {
    fontSize: 12,
    color: Colors.GRAY,
    fontWeight: "500",
  },
  breakdownValue: {
    fontSize: 12,
    fontWeight: "700",
  },
  breakdownDivider: {
    width: 1,
    height: 16,
    backgroundColor: Colors.GRAY_5,
    marginHorizontal: 12,
  },
  lastImaged: {
    fontSize: 12,
    color: Colors.GRAY,
  },
  image: {
    height: 140,
    width: 140,
    marginTop: 10,
  },
  imagePlaceholder: {
    backgroundColor: Colors.GRAY,
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
  },
  actionsRow: {
    display: "flex",
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "flex-end",
    flex: 1,
    marginTop: 15,
    gap: 10,
  },
  action: {
    padding: 10,
    borderRadius: 30,
    display: "flex",
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
  },
});

export default OxygenatorCard;
